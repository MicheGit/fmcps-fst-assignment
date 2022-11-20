# Algorithm correctness
The alghoritm used to verify the correctness of the spec is based on the Symbolic Breadth-First-Search Algorithm.
Starting from the ragion of the inital state we move through the regions by the post operation, to check if the spec is respected we verify that the new region dont have any state in common with the negation of the model, their intersection is empty.
We proceed in this way until we reach a final state or an illigal one and in this case it'll build the counterexample otherwise just confirm that the spec is respected.
# Implementation
## Building the BDD
The function start rappresenting the SMV program as an fsm_model object, combining it with the given spec it build the BDD tree.
As mentioned above in the alghortim use the nagated BDD, so it is calculated and stored in the early stage of the computation to not increse it's time complexity avoiding reduntand call.
## Definition of unsatisfied spec
In our alghoritm we define a region valid if the intersecttion between the current one and the negated tree is empty otherwise the region has at least one state that violate the invariant.
This verification is implemented in a dedicated function called <em> satisfy_spec </em> that intersect a region with negated tree and return a boolean that indicate if the intersection is empty(true) or not(false).
To verify that in our model there is no state like that we procede with a state exploartion until we reach a final state or find an illegal state:
- <strong> final state </strong>: in this case the next state of the current state will be false so by <em>isnot_false</em> we verify this condition.
- <strong> illegal state </strong>: using the <em>satisfy_spec</em> function we verify that the current state is valid
## Exploaration of BDD
The exploration is performed as a loop over the model where at each time we get the current state by method <em>post</em> and to avoid loop or usless analyses storing the states that we already visited.
To initialaize the exploration we start from the initial state of the model obtained by method <em>init</em>.
In this phase we also keep the trace of the exploration storing the current state, it will rappresent our counterexmpale in the case that the invariant is not saddisfied.
If the exploration lead to a final state, as required, the function terminate and return True and None.
# CounterExample
Otherwise it procede to build the counterexample using the stored trace.
Before starting to build the reverse path from the last reached state we verify if the model includes inputs or not cause the method <em>get_inputs_between_states</em> could rise an exception if they are not present. 
This is the same reason that drove us to not get the inputs from the last state, cause  ....(Non so come argomentare che non facciamo controllo degli input sullo stato illegale).
Starting from this state we go backwords on the trace picking at each cycle the state that allow us the transiction from the current region to the previous of the trace until the end of that.
At each iteration we add to the counter example the state and, if it's present, the input otherwise empty bracked to remark the absence of them.
Doing that we proced picking the previous region of the state.
When the analysys of the trace is ended we return false and the builded counter example.






