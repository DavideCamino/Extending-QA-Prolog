class(animal).
class(mammal).
class(polar_bear).
class(seal).
class(reindeer).
class(fish).
class(sardine).
class(bird).
class(penguin).
class(herbivore).
class(carnivore).
class(prey).
class(predator).

subclass(mammal, animal).
subclass(bird, animal).
subclass(fish, animal).
subclass(polar_bear, mammal).
subclass(seal, mammal).
subclass(reindeer, mammal).
subclass(sardine, fish).
subclass(penguin, bird).
subclass(reindeer, herbivore).


subClass(C1, C2) :-
    subclass(C1, C2).
subClass(C1, C3) :-
    subclass(C1, C2),
    subclass(C2, C3).
subClass(C1, C4) :-
    subclass(C1, C2),
    subclass(C2, C3),
    subclass(C3, C4).

disjointClasses(carnivore, herbivore).

isa(beary, polar_bear).
isa(sealy, seal).
isa(reiny, reindeer).
isa(reiny_b, reindeer).
isa(reiny_c, reindeer).
isa(sardy, sardine).
isa(penguy, penguin).

hasproperty(beary, hunt, sealy).
hasproperty(beary, hunt, penguy).
hasproperty(sealy, hunt, penguy).
hasproperty(penguy, hunt, sardy).
hasproperty(reiny, hunt, sardy).
hasproperty(reiny_b, sonOf, reiny).
hasproperty(reiny_c, sonOf, reiny_b).

ancestor1(I1, I2) :-
    hasproperty(I2, sonOf, I1).
ancestor2(I1, I2) :-
    ancestor1(I1, I3),
    hasproperty(I2, sonOf, I3).
ancestor3(I1, I2) :-
    ancestor2(I1, I3),
    hasproperty(I2, sonOf, I3).
ancestor4(I1, I2) :-
    ancestor3(I1, I3),
    hasproperty(I2, sonOf, I3).
ancestor5(I1, I2) :-
    ancestor4(I1, I3),
    hasproperty(I2, sonOf, I3).
ancestor6(I1, I2) :-
    ancestor5(I1, I3),
    hasproperty(I2, sonOf, I3).
ancestor7(I1, I2) :-
    ancestor6(I1, I3),
    hasproperty(I2, sonOf, I3).
ancestor8(I1, I2) :-
    ancestor7(I1, I3),
    hasproperty(I2, sonOf, I3).
ancestor9(I1, I2) :-
    ancestor8(I1, I3),
    hasproperty(I2, sonOf, I3).

ancestor_unfold(I1, I2) :-
    ancestor1(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor2(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor3(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor4(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor5(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor6(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor7(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor8(I1, I2).
ancestor_unfold(I1, I2) :-
    ancestor9(I1, I2).

hasProperty(I1, P, I2) :-
    hasproperty(I1, P, I2).
hasProperty(I1, ancestor,I2) :-
    ancestor_unfold(I1, I2).

isA(I, C) :-
    isa(I, C).
isA(I, C) :-
    isa(I, C2),
    subClass(C2, C).

isA(I, carnivore) :-
    hasproperty(I, hunt, _).
isA(I, predator) :-
    hasproperty(I, hunt, _).
isA(I, prey) :-
    hasproperty(_, hunt, I).


isNotA(I, C) :-
    disjointClasses(C, C2),
    isA(I, C2).

error(I, C, M) :- 
    isA(I, C),
    isNotA(I, C),
    M = 'Individual_X_cannot_belong_and_not_belong_to_class_Y'.