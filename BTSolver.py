import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation (checking to see if value removed is the only one left) and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):

        assignedVars = []
        modDict = {} 
        consistent = True
        constraints = [c for c in self.network.constraints]
        
        for c in constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)

        for v in assignedVars:
            for neighbor in self.network.getNeighborsOfVariable(v):

                if neighbor.getAssignment == v.getAssignment: 
                    consistent = False
                    break 
                
                if neighbor.isChangeable and v.getAssignment() in neighbor.getValues() and not neighbor.isAssigned():
                    self.trail.push(neighbor)
                    neighbor.removeValueFromDomain(v.getAssignment())
                    if neighbor.size() == 0:
                        consistent = False
                        break
                    else:
                        modDict[neighbor] = neighbor.getDomain()

                        for constraint in self.network.getModifiedConstraints():
                            if not constraint.isConsistent():
                                consistent = False
                                break
                            
        output = (modDict, consistent)
        return output

        # for c in self.network.constraints:
        #     for v in c.vars:
        #         if v.isAssigned():
        #             assignedVars.append(v)
        # while len(assignedVars) != 0:
        #     av = assignedVars.pop(0)
        #     for neighbor in self.network.getNeighborsOfVariable(av):
        #         if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
        #             self.trail.push(neighbor)
        #             modDict[neighbor] = neighbor.getDomain() 
        #             neighbor.removeValueFromDomain(av.getAssignment())

        # return (modDict,self.network.isConsistent())


    # =================================================================
	# Arc Consistency
	# =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
		        that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        assigned_dict = dict()
        for var in self.network.variables: 
            if var.isAssigned():
                for neighbor in self.network.getNeighborsOfVariable(var):
                    if var.getAssignment() == neighbor.getAssignment():
                        return (assigned_dict, False) 
                    if not neighbor.isAssigned() and (var.getAssignment() in neighbor.getValues()):
                        self.trail.push(neighbor)
                        neighbor.removeValueFromDomain(var.getAssignment())
                        if neighbor.size() == 0:
                            return (assigned_dict, False)
                    
                        for c in self.network.getModifiedConstraints():
                            if not c.isConsistent():
                                return (assigned_dict, False) 
                             
        n = (self.gameboard.p)*(self.gameboard.q)
        for c in self.network.getConstraints():
            counter = [0 for i in range(n)]
            for i in range(n):
                for value in c.vars[i].getValues():
                    counter[value-1] += 1
            for i in range(n):
                if counter[i] == 1:
                    for var in c.vars:
                        if var.getDomain().contains(i+1):
                            var.assignValue(i+1)
                            assigned_dict[var] = var.getAssignment()

                            for const in self.network.getModifiedConstraints():
                                if not const.isConsistent():
                                    return (assigned_dict,False)
        return (assigned_dict, True)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        empty = None
        val = 0
        min = float('inf')
        variables = [v for v in self.network.variables]
        for v in variables:
            if v.isAssigned() == 0:
                val = v.size()
                if val < min:
                    empty = v
                    min = val
        return empty 


    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        var_list = []

        degree = float("inf")
        
        unassigned_list = [x for x in self.network.variables if not x.isAssigned()]


        if len(unassigned_list) != 0:
            s_domain = min([x.size() for x in unassigned_list])
        else:
            return [None]
        
        s_unassigned = [x for x in unassigned_list if x.size() == s_domain]

        for x in s_unassigned:
            unassigned = 0
            for neighbor in self.network.getNeighborsOfVariable(x):
                if not neighbor.isAssigned():
                    unassigned +=1
            if degree > unassigned:
                degree = unassigned
                var_list = [x]
            elif degree == unassigned:
                var_list.append(x)
        return var_list

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        # lcv func go here 


        values = dict()
        for k in v.getValues():
            values[k] = 0
        
        neighbors = [neighbor for neighbor in self.network.getNeighborsOfVariable(v)]
        for selectedNeighbor in neighbors:
            if not (selectedNeighbor.isAssigned()):
                for val in selectedNeighbor.getValues():
                    if val in values:
                        values[val] += 1

        results = [] 
        sortRes = sorted(values.items(), key = lambda element: element[1])
        for key, val in sortRes:
            results.append(key)
        return results 

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
