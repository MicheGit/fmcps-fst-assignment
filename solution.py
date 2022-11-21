import pynusmv
import sys

def spec_to_bdd(model, spec):
    """
    Return the set of states of model satisfying spec, as a BDD.
    """
    bddspec = pynusmv.mc.eval_ctl_spec(model, spec)
    return bddspec

def check_explain_inv_spec(spec):
    """
    Return whether the loaded SMV model satisfies or not the invariant
    spec, that is, whether all reachable states of the model satisfies spec
    or not. Return also an explanation for why the model does not satisfy
    spec``, if it is the case, or `None otherwise.
    The result is a tuple where the first element is a boolean telling
    whether spec is satisfied, and the second element is either None if the
    first element is True``, or an execution of the SMV model violating `spec
    otherwise.
    The execution is a tuple of alternating states and inputs, starting
    and ennding with a state. States and inputs are represented by dictionaries
    where keys are state and inputs variable of the loaded SMV model, and values
    are their value.
    """
    # Step 1 - Building the BDD
    # Obtain the representation as a finite state machine
    fsm_model    = pynusmv.glob.prop_database().master.bddFsm
    # Build the BDD using the spec and the FSM
    spec_as_bdd  = spec_to_bdd(fsm_model, spec)
    negated_spec = -spec_as_bdd # We must run faster :)

    # Step 2 - Defining the safety criteria
    # Check if the current states are satisfying the spec
    def satisfy_spec(states):
        # There is any state that is not compliant with the specification
        # So it must be in the intersection between the current states and the
        # negation of the specification
        return not states.intersected(negated_spec)

    # Step 3 - Exploring the regions
    # The states we have already explored
    reached        = fsm_model.init
    # The states we are currently exploring
    current_states = fsm_model.init
    # The execution trace
    trace = [reached]

    # We perform the states exploration until we cannot reach new states or we falsify the specification
    while current_states.isnot_false() and satisfy_spec(current_states):
        # We remove the already reached states since it would be useless to check them again
        current_states = fsm_model.post(current_states) - reached
        # Add the current states to the newly added states
        reached        = reached + current_states
        # We update the execution trace
        trace.append(current_states)

    # We need to check if we have explored all the states or if we have invalidated the specification
    is_satisfied = satisfy_spec(current_states)

    # If we are satisfying the specification on every reachable states we just return true
    if is_satisfied:
        return True, None

    # Does the model support inputs?
    has_inputs = len(fsm_model.bddEnc.inputsVars) > 0

    counter_example = []
    last = fsm_model.pick_one_state(current_states.intersection(negated_spec))

    # Store the last state obiuvsly
    counter_example.append(last.get_str_values())


    # From the last state we proceed to explore backward the trace that lead us
    # to the invalid state
    next = last
    last = fsm_model.pre(next)
    # Starting from the second last state since we already picked the last in
    # the initialization
    for current in reversed(trace[:-1]):
        # We pick a state that can lead us from the *current* to the *last*
        intersect = current.intersection(last)
        state = fsm_model.pick_one_state(intersect)

        if has_inputs:
            # Get the possible inputs from the current state and the next one
            # and insert it in the counter_example
            inputs = fsm_model.get_inputs_between_states(state, next)
            counter_example.insert(0, fsm_model.pick_one_inputs(inputs).get_str_values())
        else:
            # If there is no input we insert none
            counter_example.insert(0, {})

        # Insert the current state
        counter_example.insert(0, state.get_str_values())

        # Update the next state with the current one
        next = state
        # Find the states that goes into current state
        last = fsm_model.pre(next)

    return False, counter_example

if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "filename.smv")
    sys.exit(1)

pynusmv.init.init_nusmv()
filename = sys.argv[1]
pynusmv.glob.load_from_file(filename)
pynusmv.glob.compute_model()
invtype = pynusmv.prop.propTypes['Invariant']
for prop in pynusmv.glob.prop_database():
    spec = prop.expr
    if prop.type == invtype:
        print("Property", spec, "is an INVARSPEC.")
        res, trace = check_explain_inv_spec(spec)
        if res == True:
            print("Invariant is respected")
        else:
            print("Invariant is not respected")
            print(trace)
    else:
        print("Property", spec, "is not an INVARSPEC, skipped.")

pynusmv.init.deinit_nusmv()
