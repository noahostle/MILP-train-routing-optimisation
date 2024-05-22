import gurobipy as gp
from gurobipy import GRB
import random
import time as T
import os
import subprocess
import sys

GUROBI_OUTPUT=False
TRIALS=500
#num_stations, num_trains, num_routes, minstops
types=[
	[1,2,1,3],
	[2,2,2,3],
	[3,3,3,3],
	[4,3,4,3],
	[5,3,5,3],
	[6,3,6,3],
	[7,5,7,5],
	[8,5,8,5],
	[9,5,9,5],
	[10,5,10,5],
	[11,5,11,5],
	[12,5,12,5],
	[13,5,13,5],
	[14,5,14,5],
	[15,5,15,5],
	[16,5,16,5],
	[17,5,17,5],
	[18,5,18,5],
	[19,5,19,5],
	[20,5,20,5],
	]
results=[[]*4 for i in range(len(types))]


def main():

	print("======================================================================")
	for x in range(0,TRIALS):
		trial()

	i=0
	outstr=""
	for ttype in results:
		avg=sum(ttype)/len(ttype)
		#print(f"Complexity (s*t): {types[i][0]*types[i][1]}	Stations (s): {types[i][0]}	Trains (t): {types[i][1]}")
		print(f"Train Stations: {types[i][0]}")
		rnd=round(avg,4)
		print("Average execution time: "+ format(rnd, '.4f')+ " seconds\n")
		outstr+=f"{types[i][0]}	{rnd}\n"

		i+=1
	print("======================================================================")

	#will only work on mac, i think you can use clip on win????
	subprocess.run("pbcopy", text=True, input=outstr)


def trial():
	for x in range(0,len(types)):
		results[x].append(time(types[x][0],types[x][1],types[x][2],types[x][3]))


def time(num_stations, num_trains, num_routes, minstops):
	if not GUROBI_OUTPUT:
		silence()
	start_time = T.time()
	#guro(num_stations, num_trains, num_routes, minstops)
	guro(num_stations, num_trains, num_routes, num_stations)
	end_time= T.time()
	if not GUROBI_OUTPUT:
		unsilence()

	time=end_time-start_time
	return time


def guro(num_stations, num_trains, num_routes, minstops):

	stations = [f"S{i}" for i in range(1, num_stations + 1)]
	print(stations)

	# Generate random travel times
	travel_time = {(i, j): random.randint(5, 30) for i in range(num_stations) for j in range(num_stations) if i != j}

	# Generate random schedule
	scheduled_time = {f"T{i}": random.randint(50, 100) for i in range(1, num_trains + 1)}

	# Generate max track capacities
	capacity = {(i, j): 1 for i in range(num_stations) for j in range(num_stations) if i != j}


	# Initialize the model
	model = gp.Model("train_routing")


	# Decision variables
	routes = [(i, j) for i in range(num_stations) for j in range(num_stations) if i != j]
	trains = [f"T{i}" for i in range(1, num_trains + 1)]
	x = model.addVars(routes, trains, vtype=GRB.BINARY, name="x")
	y = model.addVars(trains, vtype=GRB.INTEGER, name="y")



	# Objective: Minimize total travel time
	total_travel_time = gp.quicksum(travel_time[i, j] * x[i, j, t] for (i, j) in routes for t in trains)
	model.setObjectiveN(total_travel_time, index=0, priority=4, name="TotalTravelTime")

	# Objective: Minimize total delays
	total_delays = gp.quicksum(y[t] for t in trains)
	model.setObjectiveN(total_delays, index=1, priority=3, name="TotalDelays")



	# Constraints: flow conservation (trains cannot be destroyed or spawn at a station)
	for t in trains:
		for i in range(num_stations):
			model.addConstr(gp.quicksum(x[i, j, t] for j in range(num_stations) if i != j) == gp.quicksum(x[j, i, t] for j in range(num_stations) if i != j), name=f"FlowConservation_{i}_{t}")

	# Constraints: track capacity
	for (i, j) in routes[:num_routes]:  # Adjust here for fewre routes
		model.addConstr(gp.quicksum(x[i, j, t] for t in trains) <= capacity[(i, j)], name=f"TrackCapacity_{i}_{j}")

	# Constraints: delay calculation
	for t in trains:
		model.addConstr(y[t] >= scheduled_time[t] - gp.quicksum(travel_time[i, j] * x[i, j, t] for (i, j) in routes), name=f"DelayCalc_{t}")

	#Constraints: each train must make at least 5 stops
	for t in scheduled_time.keys():
		model.addConstr(gp.quicksum(x[i, j, t] for (i, j) in travel_time.keys()) >= minstops, name=f"AtLeastFiveStops_{t}")



	# Optimize
	model.optimize()


	# Status
	if model.status == GRB.OPTIMAL:
		print("Optimal solution found")
		for t in trains:
			print(f"Train {t}:")
			for (i, j) in routes:
				if x[i, j, t].X > 0.5:
					print(f"  Route: {i} -> {j}")
			print(f"  Delay: {y[t].X}")
	else:
		print("Failed to find optimal solution", model.status)



def silence():
	sys.stdout = open(os.devnull, 'w')

def unsilence():
	sys.stdout = sys.__stdout__

if __name__ == '__main__':
	main()

