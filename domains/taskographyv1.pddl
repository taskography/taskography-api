;; Specification of the Non-Hierarchical Taskography Rearrangement(k) Domain

(define (domain taskographyv1)
 (:requirements
  :adl
 )
 (:types
  agent
  location
  receptacle
  item
  )

 (:predicates
    ;; locations states
    (atLocation ?a - agent ?l - location)                     ; true if the agent is at the location
    (receptacleAtLocation ?r - receptacle ?l - location)      ; true if the receptacle is at the location (constant)
    (itemAtLocation ?i - item ?l - location)              ; true if the item is at the location
    
    ;; item-receptacle interaction
    (inReceptacle ?i - item ?r - receptacle)                ; true if item ?i is in receptacle ?r
    (inAnyReceptacle ?i - item)                                      ; true if item ?i is in any receptacle
    
    ;; agent-item interaction
    (holds ?a - agent ?i - item)                            ; true if item ?i is held by agent ?a
    (holdsAny ?a - agent)                                     ; true if agent ?a holds an item

    ;; receptacle types
    (receptacleOpeningType ?r - receptacle)                         ; true if receptacle ?r is an opening type
    
    ;; receptacle states
    (receptacleOpened ?r - receptacle)                        ; true if the receptacle has been opened
 )


;; ------------------------------------ MOVE AGENT ------------------------------------

;; agent goes to a location
 (:action GotoLocation
    :parameters (?a - agent ?lStart - location ?lEnd - location)
    :precondition (and (atLocation ?a ?lStart))
    :effect (and (atLocation ?a ?LEnd)
                 (not (atLocation ?a ?lStart)))
 )

 
;; ------------------------------------ RECEPTACLE STATES ------------------------------------

;; agent open receptacle
 (:action OpenReceptacle
    :parameters (?a - agent ?r - receptacle ?l - location)
    :precondition (and
        (atLocation ?a ?l)
        (receptacleAtLocation ?r ?l)
        (receptacleOpeningType ?r)
        (not (receptacleOpened ?r))
    )
    :effect (and
        (receptacleOpened ?r)
    )
 )


;; agent close receptacle
 (:action CloseReceptacle
    :parameters (?a - agent ?r - receptacle ?l - location)
    :precondition (and
        (atLocation ?a ?l)
        (receptacleAtLocation ?r ?l)
        (receptacleOpeningType ?r)
        (receptacleOpened ?r)
    )
    :effect (and
        (not (receptacleOpened ?r))
    )
 )
 

;; ------------------------------------ AGENT PICKUP  ------------------------------------
 
;; agent picks up item from ground
 (:action PickupItemNoReceptacle
    :parameters (?a - agent ?i - item ?l - location)
    :precondition (and (atLocation ?a ?l)
                       (itemAtLocation ?i ?l)
                       (not (holdsAny ?a))
                       (not (inAnyReceptacle ?i)))
    :effect (and (holdsAny ?a)
                 (holds ?a ?i)
                 (not (itemAtLocation ?i ?l)))
 )


;; agent picks up item from a non-opening receptacle
 (:action PickupItemInReceptacle
    :parameters (?a - agent ?i - item ?r - receptacle ?l - location)
    :precondition (and (atLocation ?a ?l)
                       (itemAtLocation ?i ?l)
                       (inReceptacle ?i ?r)
                       (not (receptacleOpeningType ?r))
                       (not (holdsAny ?a)))
    :effect (and (holdsAny ?a)
                 (holds ?a ?i)
                 (not (inReceptacle ?i ?r))
                 (not (inAnyReceptacle ?i))
                 (not (itemAtLocation ?i ?l)))
 )


;; agent picks up item from an opening receptacle
 (:action PickupItemInOpeningReceptacle
    :parameters (?a - agent ?i - item ?r - receptacle ?l - location)
    :precondition (and (atLocation ?a ?l)
                       (itemAtLocation ?i ?l)
                       (inReceptacle ?i ?r)
                       (receptacleOpeningType ?r)
                       (receptacleOpened ?r)
                       (not (holdsAny ?a)))
    :effect (and (holdsAny ?a)
                 (holds ?a ?i)
                 (not (inReceptacle ?i ?r))
                 (not (inAnyReceptacle ?i))
                 (not (itemAtLocation ?i ?l)))
 )


;; ------------------------------------ AGENT PLACE  ------------------------------------

;; agent places item in non-opening receptacle
 (:action PutItemInReceptacle
    :parameters (?a - agent ?i - item ?r - receptacle ?l - location)
    :precondition (and (atLocation ?a ?l)
                        (receptacleAtLocation ?r ?l)
                        (not (receptacleOpeningType ?r))
                        (holds ?a ?i))
    :effect (and (inReceptacle ?i ?r)
                 (inAnyReceptacle ?i)
                 (itemAtLocation ?i ?l)
                 (not (holdsAny ?a))
                 (not (holds ?a ?i)))
 )


 ;; agent places item in opening receptacle
 (:action PutItemInOpeningReceptacle
    :parameters (?a - agent ?i - item ?r - receptacle ?l - location)
    :precondition (and (atLocation ?a ?l)
                        (receptacleAtLocation ?r ?l)
                        (receptacleOpeningType ?r)
                        (receptacleOpened ?r)
                        (holds ?a ?i))
    :effect (and (inReceptacle ?i ?r)
                 (inAnyReceptacle ?i)
                 (itemAtLocation ?i ?l)
                 (not (holdsAny ?a))
                 (not (holds ?a ?i)))
 )

)