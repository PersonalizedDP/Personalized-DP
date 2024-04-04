# -*- coding: utf-8 -*-
import getopt
import math
import sys
import random
import cplex
import numpy as np
import time

from ctypes import c_double

def LapNoise():
    a = random.uniform(0,1)
    b = math.log(1/(1-a))
    c = random.uniform(0,1)
    if c>0.5:
        return b
    else:
        return -b

class Optimizer(cplex.callbacks.SimplexCallback):
    def __call__(self):
        value = self.get_objective_value()
        if value < self.tar:
            self.early_stop = True
            self.abort()
            
def ReadInput():
    #Store the ids of entities
    global entities
    #The connections between entities and join results
    global connections
    #The DS
    global downward_sensitivity
    #The aggregation values of join results
    global aggregation_values
    #The real query result
    global real_query_result
    #The dictionary to store the tuples' sensitivities
    entities_sensitivity_dic = {}
    #The dictionary to re-id entities
    id_dic = {}
    #The number of base table tuples
    id_num = 0
    #Collect the DS
    downward_sensitivity = 0
    #The variable is repsented one entity
    entities = []
    connections = []
    aggregation_values = []
    #read input
    
    input_file = open(input_file_path,'r')
    for line in input_file.readlines():
        elements = line.split()
        connection = []
        #The first value is the aggregation value
        aggregation_value = float(elements[0])
        #For each entity contribution to that join result
        for element in elements[1:]:
            element = int(element)
            #Re-order the IDs
            if element in id_dic.keys():
                element = id_dic[element]
            else:
                entities.append(id_num)
                id_dic[element] = id_num
                element = id_num
                id_num+=1
            #Update the entity's sensitivity
            if element in entities_sensitivity_dic.keys():
                entities_sensitivity_dic[element]+=aggregation_value
            else:
                entities_sensitivity_dic[element]=aggregation_value
            #Update the DS
            if downward_sensitivity<=entities_sensitivity_dic[element]:
                downward_sensitivity = entities_sensitivity_dic[element];                
            connection.append(element)
        connections.append(connection)
        aggregation_values.append(aggregation_value)
    real_query_result = sum(aggregation_values)
    
    
    
def LPSolver(tau, tar, LP_type = 1):
    global entities
    global connections
    global approximate_factor
    global stop_primals
    global stop_duals
    global global_max
    global aggregation_values
    global primals
    global duals

    num_constraints = len(entities)
    num_variables = len(connections)
    # Set the obj
    cpx = cplex.Cplex()
    cpx.objective.set_sense(cpx.objective.sense.maximize)
    #Set variables
    obj = np.ones(num_variables)
    ub = np.zeros(num_variables)
    for i in range(num_variables):
        ub[i]=aggregation_values[i]
    cpx.variables.add(obj=obj, ub=ub)
    #Set the right hand side and the sign
    rhs = tau
    
    senses = "L" * num_constraints
    cpx.linear_constraints.add(rhs=rhs, senses=senses)
    #Set the coefficients
    cols = []
    rows = []
    vals = []
    for i in range(num_variables):
        for j in connections[i]:
            cols.append(i)
            rows.append(j)
            vals.append(1)
    cpx.linear_constraints.set_coefficients(zip(rows, cols, vals))
    cpx.set_log_stream(None)
    cpx.set_error_stream(None)
    cpx.set_warning_stream(None)
    cpx.set_results_stream(None) 
    #Set the optimizer
    cpx.parameters.lpmethod.set(cpx.parameters.lpmethod.values.dual)

    optimizer = cpx.register_callback(Optimizer)
    optimizer.tar = tar
    optimizer.early_stop = False
    cpx.solve()
#     print(optimizer.early_stop)
    return cpx.solution.get_objective_value() 

def sample( t, B,eps, beta):
    
    ReadInput()
    start = time.time()
    n = len(entities)
    index = np.ones(n)

    result=0
    for i in range(n):
        if eps[i]<t:
            index[i] = np.random.binomial(1, (math.exp(eps[i])-1)/(math.exp(t)-1))
            
    for i in range(len(connections)):
        for j in range(len(connections[0])):
            if index[connections[i][j]]==0:
                aggregation_values[i] = 0
#     print(sum(aggregation_values))            
    T = math.ceil(math.log(B, 2))
    result=0
    for i in range(T+1):
        tau = np.ones(n)*math.pow(2,i)

        sum_tilde = LPSolver(tau, tar =result )+ T*math.pow(2, i)/t*LapNoise()-T*math.pow(2, i)/t*np.log(T/beta)
#         print(sum_tilde)
        result = max(result,sum_tilde)            
    end= time.time()
    
    return result, end-start

def main(argv):
    #The input file including the relationships between aggregations and base tuples
    global input_file_path
    input_file_path = ""
    #Privacy budget
    global epsilon
    epsilon = 0.1
    #Error probablity: with probablity at least 1-beta, the error can be bounded
    global beta
    beta = 0.1
    #The global sensitivity
    global global_sensitivity
    global_sensitivity = 1000000
    #The number of processor
    global processor_num
    processor_num = 10
    #The approximate factor
    global approximate_factor
    approximate_factor = 0
    #The real query result
    global real_query_result
    
    num_repeats = 20
    
    for i in range(6):
        input_file_path = "./Information/Q7_"+str(i)+".txt"
        ReadInput()
        times = []
        errors = []
        relative_error = []
        real_results = []
        
        B = 1000000
        n = len(entities)
        num_user = int(160000*math.pow(2, i-3))
        fc = 0.54
        fm = 0.37
        fl = 0.09
#         #Gaussian eps
#         #eps of non-zero users
#         eps = np.random.normal(1,0.3,int(n))
#         eps[eps<1/(10*math.sqrt(num_user))]=1/(10*math.sqrt(num_user))
#         # t = sum(eps)/n
#         eps_sort = np.sort(eps)

#         eps_zero = np.random.normal(1,0.3,num_user-int(n))
#         eps_zero[eps_zero<1/(10*math.sqrt(num_user))]=1/(10*math.sqrt(num_user))
#         eps_zero_sort = np.sort(eps_zero)
        
        #Uniform eps
        nc = int(n*fc)
        nm = int(n*fm)
        nl = n-nc-nm
        epsc = np.random.uniform(1/(10*math.sqrt(num_user)), 0.5, nc)
        epsm = np.random.uniform(0.5, 2, nm)
        epsl = np.ones(nl)*2
        eps = np.append(np.append(epsc, epsm), epsl)
        eps_sort = np.sort(eps)
        #to enable EM, we also need eps for zero users
        nc_z = int((num_user-n)*fc)
        nm_z = int((num_user-n)*fm)
        nl_z = (num_user-n)-nc_z-nm_z
        epsc_z = np.random.uniform(1/(10*math.sqrt(num_user)), 0.5, nc_z)
        epsm_z = np.random.uniform(0.5, 2, nm_z)
        epsl_z = np.ones(nl_z)*2
        eps_zero = np.append(np.append(epsc_z, epsm_z), epsl_z)
        eps_zero_sort = np.sort(eps_zero)

        t = (sum(eps)+sum(eps_zero))/num_user
        eps_min = min(eps_sort[0], eps_zero_sort[0])
        eps_max = max(eps_sort[n-1], eps_zero_sort[num_user-int(n)-1])
        
        for j in range(num_repeats):
            
            result,time = sample( t, B, eps, 0.1)
            error = abs(result-real_query_result)
            times.append(time)
            errors.append(error)
            relative_error.append((error)/real_query_result)


        print("result at scale = "+str(math.pow(2, i-3)))
        print("times")
        print(times)
        print("errors")
        print(errors)
        print("relative_error")
        print(relative_error)
        print("average times")
        print(sum(times)/num_repeats)
        print("average errors")
        print(sum(errors)/num_repeats)
        print("average relative_error")
        print(sum(relative_error)/num_repeats)



if __name__ == "__main__":
	main(sys.argv[1:])
