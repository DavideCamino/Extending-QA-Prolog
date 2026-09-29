# Knowledge Bases

This directory contains the knowledge bases used throughout the experiments.

Two of them are Prolog knowledge bases. To experiment with them, a Prolog interpreter is required; this guide uses [SWI-Prolog](https://www.swi-prolog.org/).

## Directory content

```
Animal_OWL_ontology.rdf
Animal_Prolog_KB.pl
Animal_QA_Prolog_compatible.pl
query_Prolog.pl
query_QA_Prolog.pl
```

## Usage

Load the original knowledge base:

```bash
swipl Animal_Prolog_KB.pl
```

Copy and paste the queries from `query_Prolog.pl` into the interpreter one at a time, and note the results.

Load the QA-Prolog compatible knowledge base:

```bash
swipl Animal_QA_Prolog_compatible.pl
```

Copy and paste the queries from `query_QA_Prolog.pl` into the interpreter one at a time.

The results obtained from the two knowledge bases are equivalent for the corresponding queries.

## Examples
 
### Example 1
 
In this example, the different definitions between the two knowledge bases are transparent to the user.
 
Original knowledge base:


```prolog
?- isA(reiny_c, C).
```

```text
C = reindeer ;
C = mammal ;
C = herbivore ;
C = animal ;
false.
```

QA-Prolog compatible knowledge base:

```prolog
?- isA(reiny_c, C).
```

```text
C = reindeer ;
C = mammal ;
C = herbivore ;
C = animal ;
false.
```

### Example 2
 
In this example, the rules differ between the two knowledge bases, but the result is logically equivalent.
 
Original knowledge base:
 
```prolog
?- error(P).
```

```
P = ['A term cannot be both true and false.', isA(reiny_a, carnivore)]
```
 
QA-Prolog compatible knowledge base:
 
```prolog
?- error(I, C, M).
```
 
```
I = reiny_a,
C = carnivore,
M = 'Individual_X_cannot_belong_and_not_belong_to_class_Y' ;
false.
```



