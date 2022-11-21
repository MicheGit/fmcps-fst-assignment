# Algorithm correctness

The proposed algorithm aims to proof the correctness of a model described by a <em>NuSMV</em> specification. Its design relies on the <em>Symbolic Breadth-First-Search Algorithm</em>.

The algorithm walks through the regions of the possible states, starting from that of the inital states, looking for an execution trace that leads to any invalid state (our counterexample). At each step it computes the possible states the model could reach. Finding a single invalid state is sufficient to demonstrate that the model doesn't respect its invariant constraints; this can be computed simply by checking whether the intersection between the possible states and the invalid states is empty or not.

In order to implement this algorithm we need a representation of the invariants, expressed as logical formulas, as a set of possible states, and therefore some common operation between sets.

# Implementation
## Step 1 - Building the [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD)

The [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) class from the pynusmv library represents regions of possibile states. Its implementation provides us the operations required to implement the algorithm.

First, the function translates the safety specification of the loaded model, initally represented a <em>[Finite State Machine](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.fsm.BddFsm)</em>, into a [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) tree. Now, we can use the [`negation operator -`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.not_) to get the tree representing the region of invalid states.

## Step 2 - Defining the safety criteria

In our algorithm we define a region valid if the intersection between the current one and the region of invalid states is empty; otherwise the region has at least one reachable state violating the safety requirements.

This predicate is defined locally by the function `satisfy_spec`, which intersects a region with the region of invalid states and returns `True` only if the result is empty.

## Step 3 - Exploring the regions

### The strategy

In this section we'll dive in the details of the exploration strategy. The idea is simple:

1. starting from the region of the initial states, the algorithm computes the possible states the model can reach after the first system tick;
2. if one of those states is an invalid one, the safety invariant is not respected;
3. otherwise, it keeps iterating until we find a final state or an invalid one.

If the property doesn't hold, the algorithm must provide a counterexample in the form of an execution trace, therefore it's useful to keep an execution trace while iterating.

One more problem rises: what if we had a loop between states? The algorithm could iterate forever, covering the same path over and over. In order to avoid such situation, the algorithm needs to ignore the states it had already taken into account.

To sum up, the algoritm will need to consider:

- the states to check;
- the states already checked;
- the regions visited along the execution.

### Implementation

<!-- CHECKED UNTIL QUI -->

The algorithm explores the reachable states. It is performed as a loop over the model where at each time we get the current state by method `post` and to avoid loop or usless analysis storing the states that we already visited.

The algorithm proceeds by steps, eventually reaching a final state or an invalid one:

- <strong> final state </strong>: the implementation of the this in this case the next state of the current state will be false so by `isnot_false` we verify this condition.
- <strong> illegal state </strong>: using the `satisfy_spec` function we verify that the current state is valid

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






