import sys
import sw_config 
import sw_lib
from dolfin import *
from dolfin_adjoint import *
from sw_utils import test_initial_condition_adjoint

set_log_level(30)
debugging["record_all"] = True

config = sw_config.SWConfiguration(nx=10, ny=2) 
period = 1.24*60*60 # Wave period
config.params["k"]=2*pi/(period*sqrt(config.params["g"]*config.params["depth"]))
config.params["basename"]="p1dgp2"
config.params["start_time"]=0
config.params["finish_time"]=period/10
config.params["dt"]=config.params["finish_time"]/10
print "Wave period (in h): ", period/60/60 
config.params["dump_period"]=100000
config.params["bctype"]="flather"

# Turbine settings
config.params["friction"]=0.0025
config.params["turbine_pos"]=[[200., 500.], [1000., 700.]]
config.params["turbine_friction"] = 12.
config.params["turbine_length"] = 400
config.params["turbine_width"] = 400

class InitialConditions(Expression):
    def __init__(self):
        pass
    def eval(self, values, X):
        values[0]=config.params['eta0']*sqrt(config.params['g']*config.params['depth'])*cos(config.params["k"]*X[0])
        values[1]=0.
        values[2]=config.params['eta0']*cos(config.params["k"]*X[0])
    def value_shape(self):
        return (3,)

W=sw_lib.p1dgp2(config.mesh)

state=Function(W)
state.interpolate(InitialConditions())

############# Turbine Field ##################
class Turbines(Expression):
    def eval(self, values, x):
        if len(config.params["turbine_pos"]) >0:
          import numpy
          friction = 0.0
          # Check if x lies in a position where a turbine is deployed and if, then increase the friction
          x_pos = numpy.array(config.params["turbine_pos"])[:,0] 
          x_pos_low = x_pos-config.params["turbine_length"]/2
          x_pos_high = x_pos+config.params["turbine_length"]/2

          y_pos = numpy.array(config.params["turbine_pos"])[:,1] 
          y_pos_low = y_pos-config.params["turbine_width"]/2
          y_pos_high = y_pos+config.params["turbine_width"]/2
          if ((x_pos_low < x[0]) & (x_pos_high > x[0]) & (y_pos_low < x[1]) & (y_pos_high > x[1])).any():
            friction += config.params["turbine_friction"] 

        values[0] = friction 
        values[1]=0.
        values[2]=0.
    def value_shape(self):
        return (3,)

tf = Function(W)
tf.interpolate(Turbines())

M,G,rhs_contr,ufl = sw_lib.construct_shallow_water(W, config.ds, config.params, turbine_field = tf[0])

functional = lambda state: dot(state, state)*dx
myj, state = sw_lib.timeloop_theta(M, G, rhs_contr, ufl, state, config.params, time_functional=functional)

adj_html("sw_forward.html", "forward")
adj_html("sw_adjoint.html", "adjoint")
sw_lib.replay(state, config.params)

J = TimeFunctional(functional(state))
adj_state = sw_lib.adjoint(state, config.params, J)

ic = Function(W)
ic.interpolate(InitialConditions())
def J(ic):
  j, state = sw_lib.timeloop_theta(M, G, rhs_contr, ufl, ic, config.params, time_functional=functional, annotate=False)
  return j

minconv = test_initial_condition_adjoint(J, ic, adj_state, seed=0.0001)
if minconv < 1.9:
  exit_code = 1
else:
  exit_code = 0
sys.exit(exit_code)