# Algorithm correctness

The alghoritm used to verify the correctness of the specification is based on the Symbolic Breadth-First-Search Algorithm.

Starting from the region of the inital state we move through the regions using the post operation, to check if the spec is respected we verify that the new region dont have any state in common with the negation of the model, their intersection is empty.

We proceed in this way until we reach a final state or an invalid one and in this case it build the counterexample. Otherwise, it will confirm that the specification is respected.

# Implementation
## Building the `BDD`

The function `start` represents the SMV program as an `fsm_model` object, combining it with the given specification it build the `BDD` tree.

As mentioned above in the alghortim use the nagated `BDD`, so it is calculated and stored in the early stage of the computation to not increse its time complexity avoiding reduntant call.

## Definition of unsatisfied specification

In our algorithm we define a region valid if the intersection between the current one and the negated tree is empty; otherwise the region has at least one state that violate the invariant.

This verification is implemented in a dedicated function, `satisfy_spec`, which intersects a region with negated tree and returns a boolean that indicate if the intersection is empty (true) or not (false).

To verify that in our model there is no state like that we proceed with a state exploartion until we reach a final state or find an illegal state:

- <strong> final state </strong>: in this case the next state of the current state will be false so by `isnot_false` we verify this condition.
- <strong> illegal state </strong>: using the `satisfy_spec` function we verify that the current state is valid

## Exploaration of `BDD`

The exploration is performed as a loop over the model where at each time we get the current state by method `post` and to avoid loop or usless analysis storing the states that we already visited.

To initialaize the exploration we start from the initial state of the model obtained by method `init`.

In this phase we also keep the trace of the exploration storing the current state, it will rappresent our counterexample in the case that the invariant is not satisfied.

If the exploration led to a final state, as required, the function terminate and return True and None.

# Counterexample

Otherwise it proceeds to build the counterexample using the stored trace.

Before starting to build the reverse path from the last reached state we verify if the model includes inputs or not because the method `get_inputs_between_states` could raise an exception if they are not present. 

This is the same reason that drove us to not get the inputs from the last state, cause  ....(Non so come argomentare che non facciamo controllo degli input sullo stato illegale).

Starting from this state we go backwards on the trace picking at each cycle the state that allows us the transition from the current region to the previous of the trace until the end of that.

At each iteration we add to the counterexample the state and, if it's present, the input otherwise empty bracked to remark the absence of them.

Doing that we proced picking the previous region of the state. When the analysys of the trace is ended we return false and the builded counterexample.






