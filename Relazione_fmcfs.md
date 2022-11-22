# Algorithm correctness

The proposed algorithm aims to proof the correctness of a model described by a <em>NuSMV</em> specification. Its design relies on the <em>Symbolic Breadth-First-Search Algorithm</em>.

The algorithm walks through the regions of the possible states, starting from that of the inital states, looking for an execution path that leads to any invalid state (our counterexample). At each step it computes the possible states the model could reach. Finding a single invalid state is sufficient to demonstrate that the model doesn't respect its invariant constraints; this can be computed simply by checking whether the intersection between the possible states and the invalid states is empty or not.

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

If the property doesn't hold, the algorithm must provide a counterexample in the form of a list of states; for that reason the function will keep note of all the possible execution paths while iterating.

One more problem rises: what if we had a loop between states? The algorithm could iterate forever, covering the same path over and over. In order to avoid such situation, the algorithm needs to ignore the states it had already taken into account.

To sum up, the algoritm will need to consider:

- the states to check;
- the states already checked;
- the regions visited along the execution.

### Implementation

The core of the algorithm is implemented as follows. In its initial configuration the region of the reached states (variable `reached`) consists in that one of the initial states. Also, those tests are the ones be checked (`current_states`), and the possible execution paths (`trace`) is initialized as a singleton list containing that region. Immediately after that, the program executes the main loop. 

The loop condition is respected only if the region of the current states is not empty ([`isnot_false`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.isnot_false)) and it doesn't contain any invalid state. Note that if it was possible to configure an invalid state as the initial configuration of the system, the loop is entirely skipped. In such case, the `trace` list trivially contains an execution that invalidates the safety requirements, consisting in that single initial configuration.

Each iteration of the loop moves a step further into the exploration. It uses the [`post`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.fsm.BddFsm.post) function over the current region in order to get the states reachable from that execution point. We can ignore all the states we have already visited, using the [`- operator`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.diff) (difference between the two). The remaining states are the ones that are to be checked the next iteration. Then the algorithm adds them ([`operator +`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.union)) to the reached states and to the execution trace.

After the last loop iteration the chances are two:
- <strong> the current region was empty </strong>: that means that every execution trace starting from an inital state led to a final state or to a loop between known valid states, so the model meets the safety requirements;
- <strong> the current region didn't satisfy the specification </strong>: that means that at least one execution could lead to a state that doesn't respect the safety requirements. 

In each case, the algorithm just needs to test whether the ending region satisfies the specification. Note that the intersection between an empty region / false [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) with another `BDD` is empty, hence an empty region satisfies any specification. In this eventuality the function can only return the tuple `(True, None)`, representing that the model respects the safety invariants.

If the last checked region and the invalid region have some state in common, then the function must build a counterexample as a list of states. 

## Step 4 - Building the counterexample

The function has to follow the execution trace backwards, starting from the last visited region. In this regions there could be both valid states and invalid ones. The algorithm can pick any of those as ending point of the counterexample.

Before starting to build the reverse path from the last reached state we verify if the model includes inputs or not because the method `get_inputs_between_states` could raise an exception if they are not present. 

The main loop considers each region in the trace in reversed order, skipping the last one. Here we find useful explaining the loop using the first iteration as an example:

1. before the first iteration, the `next` variable is the last state, the ending state of our counterexample, and the `possible_previous_states` variable contains all the possible states that could led to the last state;
2. entering the loop, the `current` variable represents the second-to-last region. In other words, this region contains the states that could be in the second-to-last position in the path. Note that a state not in this region can't be the second-to-last one;
3. the function randomly picks a state that is both in that region (`current`) and in the possible previous states. If there were inputs between such chosen predecessor and the last one (remember that `next` is the last state) those will be added to the counterexample, otherwise an empty dictionary;
4. the function appends to the head of the list the chosen predecessor and then updates the variables according to the next iteration.

It's easy to see that this behavior holds for any subsequent iteration. If the trace had only one region (if the system could be configured invalidly) the loop is skipped, because the function skips the last element and the counterexample would consist in just the last state (as it is initialized). Since the function initializes the execution trace as a singleton, it's never the case that the trace is an empty list.

At this point it is sufficient to return the tuple `(False, counter_example)` as required.

# Conclusion

In summary, this proposal of a <em>Symbolic Breadth-First-Search Algorithm</em> implementation consists in two main sections:
1. the first one follows all possible execution paths that the machine could run starting from the initial state,
2. and the second one retraces the steps of the first part, starting from one of the found invalid states and narrowing the possible paths that could led to it.






