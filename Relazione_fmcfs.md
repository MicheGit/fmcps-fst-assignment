# Overview

The proposed algorithm aims to check whether a model described by a <em>NuSMV</em> specification respects its invariants or not. In the latter case it also must provide an execution sequence that violates at least one invariant. Its design relies on the <em>Symbolic Breadth-First-Search Algorithm</em>.

The algorithm walks through the regions of the possible states, starting from that of the inital states, looking for an execution path that leads to any invalid state (our counterexample). At each step it computes the possible states the model could reach. Finding a single invalid state is sufficient to prove that the model doesn't respect its invariant constraints; in other words the model behaves correctly only if the intersection between the reachable states and the invalid states is always empty.

In order to implement this algorithm we need a representation of the invariants, expressed as logical formulas, as a set of possible states, and therefore some common operation between sets.

# Implementation
## Step 1 - Building the [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD)

The [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) class from the pynusmv library represents regions of possibile states. Its implementation provides us the operations required to implement the algorithm.

First, the function translates the safety specification of the loaded model, initally represented as a <em>[Finite State Machine](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.fsm.BddFsm)</em>, into a [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) tree. Now, we can use the [`-` operator](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.not_) to get the tree representing the region of the invalid states.

## Step 2 - Defining the safety criteria

In our algorithm we define a region valid if the intersection between the current one and the region of invalid states is empty; otherwise the region has at least one reachable state violating the safety requirements.

<p align="center">
  <img src="/images/Reachable_invalid_states.svg"
       alt="Reachable invalid states">
</p>





This predicate is defined locally by the function `satisfy_spec`, which intersects a region with the region of invalid states and returns `True` only if the result is empty.


## Step 3 - Exploring the regions

### The strategy

In this section we'll dive in the details of the exploration strategy. The idea is simple:

1. starting from the region of the initial states, the algorithm computes the possible states the model can reach after the first system tick;
2. if one of those states is an invalid one, the safety invariant is not respected;
3. otherwise, it keeps iterating until we find a final state or an invalid one.

<p align="center">
  <img src="/images/Reachable_states.svg"
       alt="Reachable states">
</p>

If the property doesn't hold, the algorithm must provide a counterexample in the form of a list of states; for that reason the function will keep note of all the possible execution paths while iterating.

One more problem rises: what if we had a loop between states? The algorithm could iterate forever, covering the same path over and over. In order to avoid such situation, the algorithm needs to ignore the states it had already taken into account.

To sum up, the algoritm will need to consider:

- the states to check;
- the states already checked;
- the regions visited along the execution.

### Implementation

The core of the algorithm is implemented as follows. In its initial configuration the region of the reached states (variable `reached`) consists in that one of the initial states. Of course, the algorithm must check even those states, so the region of the states to be checked (variable `current_states`) is initialized with them. The possible execution paths variable (`trace`) is initialized as a singleton list containing that region, since they are the starting points. Immediately after that, the program executes the main loop. 

The loop condition is respected only if the region of the current states is not empty ([`isnot_false`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.isnot_false)) and it doesn't contain any invalid state. Note that if it was possible to configure an invalid state as the initial configuration of the system, the loop is entirely skipped. In such case, the `trace` list trivially contains an execution that invalidates the safety requirements, consisting in that single initial configuration.

Each iteration of the loop moves a step further into the exploration. It gets the states reachable from the states in the current region using the [`post`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.fsm.BddFsm.post) function. We can ignore all the states we have already visited, using the [`-` operator](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.diff) (difference between the two). The remaining states are the ones that are to be checked in the next iteration. Then the algorithm registers them as reached ([`+` operator](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD.union) on `reached`) and appends them to the execution trace.

After the last loop iteration there are two cases:
- **the current region was empty**: that means that every execution trace starting from an inital state led either to a final state or to a loop including only valid states, so the model meets the safety requirements;
- **the current region didn't satisfy the specification**: that is, at least one execution may lead to a state that doesn't respect the safety requirements. 

In each case, the algorithm just needs to test whether the ending region satisfies the specification. Note that the intersection between an empty region / false [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) with another `BDD` is empty, hence an empty region satisfies any specification. In this eventuality the function can only return the tuple `(True, None)`, representing that the model respects the safety invariants.

If the last checked region and the invalid region share some state, then the function must provide a counterexample as a list of states. 

## Step 4 - Building the counterexample

The function follows the execution trace backwards, starting from the last visited region. In this regions there could be both valid states and invalid ones. The algorithm can safely pick any of those as ending point of the counterexample.

Before starting to build the reverse path from the last reached state we verify whether the model accepts inputs or not, because in such case the method `get_inputs_between_states` raises an exception if they are not supplied. 

The main loop considers each region in the trace in reversed order, skipping the last one. Here we find useful to explain how the loop deals the first iteration, as an example:

1. before the first iteration, the `next` variable is the final state of our counterexample and the `possible_previous_states` variable contains all the possible states that could lead to the last state; 
<p align="center">
  <img src="/images/Counter_example_1.svg"
       alt="Initialization phase for the counter example">
</p>

2. entering the loop, the `current` variable represents the second-to-last region. In other words, this region contains all and only the states that could be in the second-to-last position in the path;
3. the function randomly picks a state that is both in that region (`current`) and in the possible previous states. If there were inputs between such chosen predecessor and the last one (remember that `next` is the final state in this example) those will be added to the counterexample, otherwise an empty dictionary;
4. the function appends to the head of the list the chosen predecessor and then updates the variables according to the next iteration.

<p align="center">
  <img src="/images/Counter_example_2.svg"
       alt="Iteration for the counter example">
</p>

It's easy to see that this behaviour holds for any subsequent iteration. If the trace had only one region (if the system could be configured invalidly) then the loop is skipped: the counterexample would contain only the last state (as it would have been initialized). Since the function initializes the execution trace as a singleton, it's never the case that the trace is an empty list.

At this point it is sufficient to return the tuple `(False, counter_example)` as required.

# Algorithm correctness

The formal proof follows the algorithm as implemented in the function `check_explain_inv_spec` in the file `solution.py`, and consists in a close look up into the details of the two main loops of the algorithm.

## First loop (step 3)

The first loop act over:
- the `current_states` variable, a [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) representing the region of the new found reachable states;
- the `reached` variable, representing the region of all the already reached states.
- the `trace` variable, an ordered list of the regions reached for each transition simulated.

The **loop condition** is verified when `current_states` is not empty and does not overlap the invalid region, i.e. there is no invalid state in it.

The **loop invariant** for each variable at the iteration *i* is:
- in `current_states` there are only states reachable from the region considered in the iteration *i-1* such that were not reached by any iteration *j < i*;
- `reached` represents all the states reached in all the previous iterations;
- `trace` is a list with *i+1* nodes s.t. the node *k* holds the states reached by the iteration *k*.

The proof follows by induction:
- **Base case** - the base case depicts the state of the algorithm before the first loop iteration, but conceptually after having reached the initial states:
  - `current_states = fsm_model.init` - the invariant holds vacuosly, because the algorithm performed no step of the loop and those states are the initial ones;
  - `reached = fsm_model.init` - the invariant holds because in this situation the only reached states are the initial ones;
  - `trace = [reached]` - the invariant holds for the same reason as above.
- **Inductive case**:
  - `current_states = fsm_model.post(current_states) - reached` - the `post` function returns the states reachable from the current region. Since by inductive hypothesis `reached` represents all previously met states, the difference between the new ones and `reached` meets the invariant condition for `current_states`;
  - `reached = reached + current_states` - by i.h., `reached` represents all the states reached by all the *i - 1* previous iterations, therefore adding the current ones respects the invariant for the *i*th iteration;
  - `trace.append(current_states)` - similarly as above, by i.h. `trace` is a well formed list of *i* nodes. Therefore, appending the current states as last element is enough to keep holding the invariant, since the current states are the ones reached from the *i*th node of `trace`.

**Post condition** - There are two main cases that falsify the loop condition:
- 1: `current_states` is empty, therefore the loop considered at least once all the reachable states from the initial configuration, and none of them violated the requirements. In such case, the algorithm returns the `True, None` tuple. 
- 2: `current_states` is not empty and there is an overlap with the invalid states. In such case, since the invariant holds, we have a `trace` that is a list with *i+1* nodes, where *i* is the number of the loops performed, i.e. the number of transitions that would need in order to reach an invalid state; theremore each node *k* of the `trace` has a [`BDD`](https://pynusmv.readthedocs.io/pynusmv.html#pynusmv.dd.BDD) that represents the states reachable after *k-1* transitions, in particular, reachable from the *k-1*th node. So, among those states there are the ones that lead to the invalid one(s) in the last node.

**Termination** - This always converges because:
- in the first case the algorithm visited all the reachable states only once. Since the number of such states is finite, the algorithm eventually converges;
- in the second case the loop quits programmatically finding a counterexample.

## Second loop (Step 4)

The second loop acts over:
- a variable `counter_example`, which is a list of states (represented as a python dictionary), and it represents an execution trace that represents the sequence of states ending in an invalid one;
- a variable `next`, that represents the state picked in the current iteration;
- a variable `possible_previous_states` that enumerates all the possible previous steps.

The second loop executes one iteration step for each node of the found `trace` backwards, minus the last one which is used for the initialization. We can see the `trace` as a counterexample we know
- the number of transitions required;
- the possible states after (and before) each transition.

Thus, the loop condition can be informally expressed as "loop until all the trace steps are specified".

**Loop invariant**:
- `counter_example` holds all the states between the current `trace` node and the final, invalid, state;
- `next` is the state picked in the current iteration;
- `possible_previous_states` represents the states that could led to `next` in one transition.

The proof follows by induction:
**Base case** - such that the last (invalid) state has been taken into account yet:
- `counter_example = [last_state.get_str_values()]` - the invariant holds since `last_state` is a state picked from the reachable states after the final transition (the last region in `trace`) intersected with the invalid states (so we are sure that is invalid) and since the 
- `next = last_state` - the invariant holds because, for the same reasons as above, `last_state` is the legitimate last state of the counter example;
- `possible_previous_states = fsm_model.pre(next)` - the invariant holds trivially.

**Inductive case** - in the loop body a predecessor of `next` is randomly chosen (`chosen_pre`) among all the states of the current `trace` node and the `possible_previous_states`. Then the counterexample is updated inserting as head `inputs`, a possible set of inputs that can lead from `chosen_pre` to `next` when the model accepts inputs, otherwise it is an empty python dictionary. By i.h., `counter_example` contains all the transitions and inputs that can lead from `next` to the last state; after that operation `counter_example` contains also the inputs accepted by the current state (`next`):
- `counter_example.insert(0, chosen_pre.get_str_values())` - since all the precondition listed above, the counterexample now holds all the transitions from `chosen_pre` to the last state;
- `next = chosen_pre` - `next` is the state to be considered in the next iteration, which is the `trace` node before this one;
- `possible_previous_states = fsm_model.pre(next)` - it holds trivially.

**Post condition**:
Since the only way to exit the loop is running out of nodes in the `trace`, `counter_example` contains a trace that starts from an initial state (since the initial state has to be picked from the first node of `trace`) end ends up in the last state (the invalid one). Since all those states are picked from a region in the `trace`, the so found counterexample is proven to be the same that led to the invalid state in the first place.

# Recap

In summary, this proposal of a <em>Symbolic Breadth-First-Search Algorithm</em> implementation consists in two main sections:
1. the first one follows all possible execution paths that the machine could run starting from the initial state,
2. and the second one retraces the steps of the first part, starting from one of the found invalid states and narrowing the possible paths that could led to it.







