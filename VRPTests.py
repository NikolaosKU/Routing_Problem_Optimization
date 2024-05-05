from DatasetClasses import DatasetReader
from RoutingProblem import RoutingProblem
from Distances import get_straight_line_distance_matrix, get_route_straight_line_distance
from Solvers import get_cvrp_solution
from OSRM import osrm_get_matrix
import pandas as pd

dataset_name = 'DATASET_SERVICEFREQS_NODUP_20240405.csv'
dataset = DatasetReader(file=dataset_name)

metrics_df = None

for day in range(1, 7):
    # CREATE A ROUTING PROBLEM
    routing_problem = RoutingProblem('DAY_'+str(day))
    print(day)
    if routing_problem.is_saved():
        routing_problem.load()
    else:
        # CALCULATE STOPS, SOLUTION AND DEMANDS
        coordinates, original_solution, demand_stops, demand_containers = dataset.get_cvrp_data(day)
        routing_problem.add_coordinates(coordinates)
        routing_problem.add_solution('original', original_solution)
        routing_problem.set_demands(demand_stops)
        
        # CALCULATE CAPACITIES
        nb_trucks = dataset.get_nb_trucks_of_day(day)
        nb_stops = dataset.get_nb_stops_of_day(day)
        nb_containers = dataset.get_nb_containers_of_day(day)
        capacity_stops = [round(nb_stops/nb_trucks) + 2]*nb_trucks 
        capacity_containers = [round(nb_containers/nb_trucks) + 5]*nb_trucks
        routing_problem.set_capacities(nb_trucks, capacity_stops)

        # CALCULATE DISTANCE MATRIX
        straight_line_matrix = get_straight_line_distance_matrix(coordinates)
        routing_problem.add_distance_matrix('straight-line', straight_line_matrix)
        osrm_dist, osrm_time = osrm_get_matrix(routing_problem.get_coordinates())
        routing_problem.add_distance_matrix('osrm-distance', osrm_dist)
        routing_problem.add_distance_matrix('osrm-time', osrm_time)
        
        # Solve the CVRP with straight line
        straight_line_solution = get_cvrp_solution(routing_problem.get_distance_matrix('straight-line'), routing_problem.get_nb_vehicles(), routing_problem.get_capacities(), routing_problem.get_demands())
        routing_problem.add_solution('straight_line_solution', straight_line_solution)
        print('straight line done')
        # Solve the CVRP with OSRM Distance
        solution_osrm_dist_indices = get_cvrp_solution(routing_problem.get_distance_matrix('osrm-distance'), routing_problem.get_nb_vehicles(), routing_problem.get_capacities(), routing_problem.get_demands())
        routing_problem.add_solution('osrm-distance', solution_osrm_dist_indices)
        print('osrm distance done')
        # Solve the CVRP with OSRM Time
        solution_osrm_time_indices  = get_cvrp_solution(routing_problem.get_distance_matrix('osrm-time'), routing_problem.get_nb_vehicles(), routing_problem.get_capacities(), routing_problem.get_demands())
        routing_problem.add_solution('osrm-time', solution_osrm_time_indices)
        print('osrm time done')

        # SAVE VRP
        routing_problem.save()



    routing_problem.plot(real=True)
    routing_problem_metrics_df = routing_problem.get_metrics(original_solution_name='original', add_osrm_route_metric=True)
    if metrics_df is None:
        metrics_df = routing_problem_metrics_df
    else:
        metrics_df = pd.concat([metrics_df, routing_problem_metrics_df])
    print(metrics_df)

metrics_df.to_csv('solution_metrics_cvrp.csv', sep=';', index=False)