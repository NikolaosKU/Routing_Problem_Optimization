"""
Functions to solve vehicle routing problems.
"""
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def get_tsp_solution(distance_matrix):

    """Stores the data for the problem."""
    data = {
            "distance_matrix": distance_matrix,
            "num_vehicles": 1,
            "depot": 0
            }

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    #search_parameters.time_limit.seconds = 20
    

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Save sequence of stops.
    if solution:
        output = {}
        index = routing.Start(0)
        route_indices = []
        while not routing.IsEnd(index):
            route_indices.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        route_indices.append(manager.IndexToNode(index))
        output["TSP_1"] = route_indices
        return output
    
    else:
        return {}

def get_cvrp_solution(distance_matrix, nb_vehicles, capacities, demands):
    
    # Stores data of model
    data = {}
    data["distance_matrix"] = distance_matrix
    data["demands"] = demands
    data["vehicle_capacities"] = capacities
    data["num_vehicles"] = nb_vehicles
    data["depot"] = 0
    
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

     # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,       # no slack
        100000,  # vehicle maximum travel distance
        True,    # start cumul to zero
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(1000)

    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data["vehicle_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        "Capacity",
    )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(100)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        output = {}
        for vehicle_id in range(data["num_vehicles"]):
            index_list = []
            index = routing.Start(vehicle_id)
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                index_list.append(node_index)
                index = solution.Value(routing.NextVar(index))
            index_list.append(manager.IndexToNode(index))
            output["truck_" + str(vehicle_id)] = index_list
        return output
    else:
        print("no solution")
        return {}