import numpy
from dolfin import info_blue, Constant
import dolfin
from helpers import info, info_green, info_red, info_blue

# The wrapper class of the objective/constaint functions that as required by the ipopt package
class  IPOptFunction(object):

  def __init__(self):
    pass

  def objective(self, x):
    ''' The objective function evaluated at x. '''
    print "The objective_user function must be overloaded."

  def gradient(self, x):
    ''' The gradient of the objective function evaluated at x. '''
    print "The gradient_user function must be overloaded."

  def constraints(self, x):
    ''' The constraint functions evaluated at x. '''
    return numpy.array([])

  def jacobian(self, x):
    ''' The Jacobian of the constraint functions evaluated at x. '''
    return (numpy.array([]), numpy.array([]))

def deploy_turbines(config, nx, ny, friction=21.):
    ''' Generates an array of initial turbine positions with nx x ny turbines homonginuosly distributed over the site with the specified dimensions. '''
    turbine_pos = []
    for x_r in numpy.linspace(config.domain.site_x_start + 0.5*config.params["turbine_x"], config.domain.site_x_end - 0.5*config.params["turbine_y"], nx):
        for y_r in numpy.linspace(config.domain.site_y_start + 0.5*config.params["turbine_x"], config.domain.site_y_end - 0.5*config.params["turbine_y"], ny):
            turbine_pos.append((float(x_r), float(y_r)))
    config.set_turbine_pos(turbine_pos, friction)
    info_blue("Deployed " + str(len(turbine_pos)) + " turbines.")
    return turbine_pos

def position_constraints(config):
    ''' This function returns the constraints to ensure that the turbine positions remain inside the domain plus an optional spacing. '''

    n = len(config.params["turbine_pos"])
    lc = []
    lb_x = config.domain.site_x_start + config.params["turbine_x"]/2 
    lb_y = config.domain.site_y_start + config.params["turbine_y"]/2 
    ub_x = config.domain.site_x_end - config.params["turbine_x"]/2 
    ub_y = config.domain.site_y_end - config.params["turbine_y"]/2 

    if not lb_x < ub_x or not lb_y < ub_y:
        raise ValueError, "Lower bound is larger than upper bound. Is your domain large enough?"
  
    # The control variable is ordered as [t1_x, t1_y, t2_x, t2_y, t3_x, ...]
    lb = n * [Constant(lb_x), Constant(lb_y)]
    ub = n * [Constant(ub_x), Constant(ub_y)]
    return lb, ub 

def friction_constraints(config, lb = 0.0, ub = None):
    ''' This function returns the constraints to ensure that the turbine friction controls remain reasonable. '''

    if ub != None and not lb < ub:
        raise ValueError, "Lower bound is larger than upper bound."
    
    if ub == None:
      ub = 10**12

    n = len(config.params["turbine_pos"])
    return n * [Constant(lb)], n * [Constant(ub)] 

def get_minimum_distance_constraint_func(config, min_distance = None):
    if not 'turbine_pos' in config.params['controls']:
        raise NotImplementedError, "Inequality contraints for the distance only make sense if the turbine positions are control variables."

    if not min_distance:
        min_distance = 1.5*max(config.params["turbine_x"], config.params["turbine_y"])

    def l2norm(x):
        return sum([v**2 for v in x])

    def f_ieqcons(m):
        ieqcons = []
        if len(config.params['controls']) == 2:
        # If the controls consists of the the friction and the positions, then we need to first extract the position part
          assert(len(m)%3 == 0)
          m_pos = m[len(m)/3:]
        else:
          m_pos = m

        for i in range(len(m_pos)/2):
            for j in range(len(m_pos)/2):                                                                       
                if i <= j:
                    continue
                ieqcons.append(l2norm( [m_pos[2*i]-m_pos[2*j], m_pos[2*i+1]-m_pos[2*j+1]] ) - min_distance**2)              
        return numpy.array(ieqcons)

    def fprime_ieqcons(m):
        ieqcons = []
        if len(config.params['controls']) == 2:
          # If the controls consists of the the friction and the positions, then we need to first extract the position part
          assert(len(m)%3 == 0)
          m_pos = m[len(m)/3:]
          mf_len = len(m_pos)/2
        else:
          m_pos = m
          mf_len = 0

        for i in range(len(m_pos)/2):
            for j in range(len(m_pos)/2):
                if i <= j:
                    continue
                prime_ieqcons = numpy.zeros(len(m))

                # The control vector contains the friction coefficients first, so we need to shift here
                prime_ieqcons[mf_len + 2*i] = 2*(m_pos[2*i]-m_pos[2*j])
                prime_ieqcons[mf_len + 2*j] = -2*(m_pos[2*i]-m_pos[2*j])
                prime_ieqcons[mf_len + 2*i+1] = 2*(m_pos[2*i+1]-m_pos[2*j+1])
                prime_ieqcons[mf_len + 2*j+1] = -2*(m_pos[2*i+1]-m_pos[2*j+1])

                ieqcons.append(prime_ieqcons)
        return numpy.array(ieqcons)

    return {'type': 'ineq', 'fun': f_ieqcons, 'jac': fprime_ieqcons} 

def plot_site_constraints(config, vertices):
    
    ineqs = []
    for p in range(len(vertices)):
        # x1 and x2 are the two points that describe one of the sites edge 
        x1 = numpy.array(vertices[p])
        x2 = numpy.array(vertices[(p+1)%len(vertices)])
        c = x2-x1
        # Normal vector of c
        n = [c[1], -c[0]]

        ineqs.append((x1, n))
    
    class SiteConstraintExpr(dolfin.Expression):
        def eval(self, value, x):
            inside = True
            for x1, n in ineqs:
                # So the inequality for this edge is: g(x) := n^T.(x1-x) >= 0 
                inside = inside and (numpy.dot(n, x1-x) >= 0)
            
            value[0] = int(inside)
    
    f = dolfin.project(SiteConstraintExpr(), config.turbine_function_space)
    out_file = dolfin.File("site_constraints.pvd", "compressed")
    out_file << f

def generate_site_constraints(config, vertices, penalty_factor=1e3):
    ''' Generates the inequality constraints for generic polygon constraints. The parameter polygon 
        must be a list of point coorinates that describes the site edges in anti-clockwise order. '''

    # To begin with, lets save a vtu that visualises the constraints
    plot_site_constraints(config, vertices)

    def f_ieqcons(m):
        ieqcons = []
        if len(config.params['controls']) == 2:
        # If the controls consists of the the friction and the positions, then we need to first extract the position part
          assert(len(m)%3 == 0)
          m_pos = m[len(m)/3:]
        else:
          m_pos = m

        for i in range(len(m_pos)/2):                                                                           
            for p in range(len(vertices)):
                # x1 and x2 are the two points that describe one of the sites edge 
                x1 = numpy.array(vertices[p])
                x2 = numpy.array(vertices[(p+1)%len(vertices)])
                c = x2-x1
                # Normal vector of c
                n = [c[1], -c[0]]

                # So the inequality for this edge is: g(x) := n^T.(x1-x) >= 0 
                x = m_pos[2*i:2*i+2]
                ieqcons.append(penalty_factor*numpy.dot(n, x1-x))

        return numpy.array(ieqcons)

    def fprime_ieqcons(m):
        ieqcons = []
        if len(config.params['controls']) == 2:
          # If the controls consists of the the friction and the positions, then we need to first extract the position part
          assert(len(m)%3 == 0)
          m_pos = m[len(m)/3:]
          mf_len = len(m_pos)/2
        else:
          mf_len = 0
          m_pos = m

        for i in range(len(m_pos)/2):
            for p in range(len(vertices)):
                # x1 and x2 are the two points that describe one of the sites edge 
                x1 = numpy.array(vertices[p])
                x2 = numpy.array(vertices[(p+1)%len(vertices)])
                c = x2-x1
                # Normal vector of c
                n = [c[1], -c[0]]

                prime_ieqcons = numpy.zeros(len(m))

                # The control vector contains the friction coefficients first, so we need to shift here
                prime_ieqcons[mf_len + 2*i] = -penalty_factor*n[0] 
                prime_ieqcons[mf_len + 2*i+1] = -penalty_factor*n[1] 

                ieqcons.append(prime_ieqcons)
        return numpy.array(ieqcons)

    return {'type': 'ineq', 'fun': f_ieqcons, 'jac': fprime_ieqcons} 
