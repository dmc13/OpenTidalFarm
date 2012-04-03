'''This tests checks the corrections of the adjoint by using it to compute the 
   derivative of the functional with respect to the friction field.'''

import sys
import configuration 
import numpy
from utils import test_gradient_array
from reduced_functional import *
set_log_level(PROGRESS)

# We set the perturbation_direction with a constant seed, so that it is consistent in a parallel environment.
numpy.random.seed(21) 

# Create the model configuration
config = configuration.DefaultConfiguration(nx=30, ny=15)
period = 1.24*60*60 # Wave period
config.params["k"] = 2*pi/(period*sqrt(config.params["g"]*config.params["depth"]))
# Start at rest state
config.params["start_time"] = period/4 
config.params["finish_time"] = 2./4*period
config.params["dt"] = config.params["finish_time"]/5
print "Wave period (in h): ", period/60/60 
config.params["dump_period"] = 1000
config.params["verbose"] = 0
# Turbine settings
config.params["friction"] = 0.0025
config.params["turbine_pos"] = [[1000., 500.], [1600, 300], [2500, 700]]
# The turbine friction is the control variable 
config.params["turbine_friction"] = 12.0*numpy.random.rand(len(config.params["turbine_pos"]))
config.params["turbine_x"] = 200
config.params["turbine_y"] = 400

# Set up the model 
model = ReducedFunctional(config)
m0 = model.initial_control()

# Run the taylor test
# Choose a random direction
p_rand = numpy.random.rand(len(config.params['turbine_friction']) + 2*len(config.params['turbine_pos']))
p_f = numpy.zeros(len(p_rand))
# Peturb the friction of the first turbine only.
p_f[0] = 1.
i = len(config.params['turbine_friction'])
# Peturb the x position of the first turbine only.
p_x = numpy.zeros(len(p_rand))
p_x[i] = 1.
# Peturb the y position of the first turbine only.
p_y = numpy.zeros(len(p_rand))
p_y[i+1] = 1.
for p in (p_rand, p_f, p_x, p_y):
  print "Running derivative test in direction", p 
  minconv = test_gradient_array(model.j, model.dj, m0, seed=0.01, perturbation_direction=p)
  if minconv < 1.98:
    sys.exit(1)
