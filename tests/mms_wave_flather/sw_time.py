import sys
from opentidalfarm import *
from opentidalfarm.initial_conditions import SinusoidalInitialCondition
from dolfin_adjoint import adj_reset 
from math import log

set_log_level(PROGRESS)
parameters["std_out_all_processes"] = False;

def error(config, eta0, k):
  state = Function(config.function_space)
  state.interpolate(SinusoidalInitialCondition(config, eta0, k, config.params["depth"]))

  adj_reset()
  shallow_water_model.sw_solve(config, state, annotate=False)

  analytic_sol = Expression(("eta0*sqrt(g/depth)*cos(k*x[0]-sqrt(g*depth)*k*t)", \
                             "0", \
                             "eta0*cos(k*x[0]-sqrt(g*depth)*k*t)"), \
                             eta0=config.params["eta0"], g=config.params["g"], \
                             depth=config.params["depth"], t=config.params["current_time"], k=config.params["k"])
  exactstate = Function(config.function_space)
  exactstate.interpolate(analytic_sol)
  e = state - exactstate
  return sqrt(assemble(dot(e,e)*dx))

def test(refinment_level):
  config = DefaultConfiguration(nx=2**8, ny=2, finite_element = finite_elements.p1dgp2) 
  eta0 = 2.0
  k = pi/config.domain.basin_x
  config.params["finish_time"] = pi/(sqrt(config.params["g"]*config.params["depth"])*k)
  config.params["dt"] = config.params["finish_time"]/(2*2**refinment_level)
  config.params["theta"] = 0.5
  config.params["dump_period"]=100000

  return error(config, eta0, k)

errors = []
tests = 6
for refinment_level in range(1, tests):
  errors.append(test(refinment_level))
# Compute the order of convergence 
conv = [] 
for i in range(len(errors)-1):
  conv.append(abs(log(errors[i+1]/errors[i], 2)))

info("Temporal order of convergence (expecting 2.0): %s" % str(conv))
if min(conv)<1.8:
  info_red("Temporal convergence test failed for wave_flather")
  sys.exit(1)
else:
  info_green("Test passed")
