import pynusmv
import sys

def pretty_print_trace(trace):
    """
    A trace is a list of dictionaries. This function prints the 
    list as nusmv would
    """
    last_printed = dict()
    for i in range(0, len(trace)):
        step = trace[i]
        if "inputs" in step:
            print("-------INPUTS {} ------".format(i + 1))
            for key in step["inputs"]:
                if last_printed.get(key) != step["inputs"].get(key):
                    # We are not going to print duplicate values
                    print("\t{} = {}".format(key, step["inputs"].get(key)))
            last_printed.update(step["inputs"])

        print("-------STATE {} ------".format(i + 1))
        for key in step["state"]:
            if last_printed.get(key) != step["state"].get(key):
                # We are not going to print duplicate values
                print("\t{} = {}".format(key, step["state"].get(key)))
        last_printed.update(step["state"])


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

    # Obtain the representation as a finite state machine
    fsm_model    = pynusmv.glob.prop_database().master.bddFsm
    # Build the BDD using the spec and the FSM
    spec_as_bdd  = spec_to_bdd(fsm_model, spec)
    negated_spec = -spec_as_bdd # We must run faster :)

    # Check if the current states are satisfying the spec
    def satisfy_spec(states):
        # There is any state that is not compliant with the specification
        # So it must be in the intersection between the current states and the
        # negation of the specification
        return not states.intersected(negated_spec)

    # The states that we already have explored
    reached        = fsm_model.init
    # The states that we are currently exploring
    current_states = fsm_model.init
    # The esecution trace
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

    # We check if inputs are supported (IVAR)
    accepts_input = len(fsm_model.bddEnc.inputsVars) > 0

    # We pick all the final states that invalidate the spec
    invalid_final_states = fsm_model.pre(trace[-1])

    # We choose one of the invalid states that we reached
    #  starting from it, we will retrace our steps to the init state
    next_state = fsm_model.pick_one_state(invalid_final_states)
    previous_states = fsm_model.pre(next_state)
    counter_example = [{
        "state": next_state.get_str_values()
    }]
    # We follow the execution trace in reverse order skipping the last two sets of states
    #   - the last one because it is a false bdd
    #   - the second-to-last one because we picked the last state from it
    for current_states in reversed(trace[:-1]):
        # We get a state that we could have come from
        chosen_state = fsm_model.pick_one_state(current_states.intersection(previous_states))

        # Update the counter example with the current state + transition that got us there
        trace_node = {
            "state": chosen_state.get_str_values()
        }

        if accepts_input:
            possible_inputs = fsm_model.get_inputs_between_states(chosen_state, next_state)
            trace_node.update({
                "inputs": fsm_model.pick_one_inputs(possible_inputs).get_str_values()
            })

        # We move to the previous step in the trace...
        counter_example.append(trace_node)
        next_state = chosen_state
        previous_states = fsm_model.pre(chosen_state)
    
    # We need to reverse the counterexample list

    counter_example = list(reversed(counter_example))
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
            pretty_print_trace(trace)
    else:
        print("Property", spec, "is not an INVARSPEC, skipped.")

pynusmv.init.deinit_nusmv()
