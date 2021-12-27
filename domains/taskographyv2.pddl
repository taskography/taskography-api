;; Specification of the Hierarchical Taskography Rearrangement(k) Domain

(define (domain taskographyv2)
 (:requirements
  :adl
 )
 (:types
  agent
  room
  place
  location
  receptacle
  item
  )

 (:predicates
    ;; locations states
    (inRoom ?a - agent ?r - room)                             ; true if the agent is in the room
    (inPlace ?a - agent ?p - place)                             ; true if the agent is in the place
    (atLocation ?a - agent ?l - location)                     ; true if the agent is at the location
    (receptacleAtLocation ?r - receptacle ?l - location)      ; true if the receptacle is at the location (constant)
    (itemAtLocation ?i - item ?l - location)              ; true if the item is at the location
    (placeInRoom ?p - place ?r - room)                 ; true if the place is in the room
    (locationInPlace ?l - location ?p - place)                 ; true if the location is in the place
    (roomPlace ?p - place ?r - room)                    ; true if the place is the door (center) of the room
    (placeLocation ?l - location ?p - place)                    ; true if the location is the center point of the place

    ;; room-room motion constraints
    (roomsConnected ?r1 - room ?r2 - room)                                 ; true if rooms ?r1 and ?r2 are connected
    
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

;; agent goes to room
 (:action GoToRoom
     :parameters (?a - agent ?rStart - room ?rEnd - room ?pStart - place ?pEnd - place ?lStart - location ?lEnd - location)
     :precondition (and (inRoom ?a ?rStart)
                        (inPlace ?a ?pStart)
                        (atLocation ?a ?lStart)
                        ; agent starts and ends at doors
                        (roomPlace ?pStart ?rStart)
                        (placeInRoom ?pStart ?rStart)
                        (placeLocation ?lStart ?pStart)
                        (locationInPlace ?lStart ?pStart)
                        (roomPlace ?pEnd ?rEnd)
                        (placeInRoom ?pEnd ?rEnd)
                        (placeLocation ?lEnd ?pEnd)
                        (locationInPlace ?lEnd ?pEnd)
                        ; rooms must be connected
                        (roomsConnected ?rStart ?rEnd)
     )
     :effect (and (inRoom ?a ?rEnd)
                  (inPlace ?a ?pEnd)
                  (atLocation ?a ?lEnd)
                  (not (inRoom ?a ?rStart))
                  (not (inPlace ?a ?pStart))
                  (not (atLocation ?a ?lStart))
     )
 )
 

;; agent goes to place
 (:action GoToPlace
     :parameters (?a - agent ?pStart - place ?pEnd - place ?lStart - location ?lEnd - location ?r - room)
     :precondition (and (inRoom ?a ?r)
                        (inPlace ?a ?pStart)
                        (atLocation ?a ?lStart)
                        ; agent starts and ends at place centers
                        (placeInRoom ?pStart ?r)
                        (placeLocation ?lStart ?pStart)
                        (locationInPlace ?lStart ?pStart)
                        (placeInRoom ?pEnd ?r)
                        (placeLocation ?lEnd ?pEnd)
                        (locationInPlace ?lEnd ?pEnd)
     )
     :effect (and (inPlace ?a ?pEnd)
                  (atLocation ?a ?lEnd)
                  (not (inPlace ?a ?pStart))
                  (not (atLocation ?a ?lStart))
     )
 )


;; agent goes to a location
 (:action GotoLocation
    :parameters (?a - agent ?lStart - location ?lEnd - location ?p - place)
    :precondition (and (inPlace ?a ?p)
                       (atLocation ?a ?lStart)
                       (locationInPlace ?lStart ?p)
                       (locationInPlace ?lEnd ?p))
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