---
layout: default
---

About OpenTidalFarm 
===================
OpenTidalFarm is a layout optimisation software for tidal turbine farms.

Problem 

Accurate simulations

With advanced numerical techniques, OpenTidalFarm is able optimise hundreds of turbines.

It is open source software can be downloaded and used for free.

Features 
========
* High resolution shallow water model for accurate flow prediction
* Arbitrary shoreline data
* Optimization for power output
* Site constraints / minimum distance between turbines
* Up to multiple hundered turbines

For additional features such as bathymetry support, enforcing a minimum/maximum turbine installation depth and cable costs please [contact me](#contact). 
 
Examples
========
<iframe class="youtube-player" type="text/html" width="640" height="385" src="http://www.youtube.com/embed/ng3bbso-vGk" frameborder="0">
</iframe>

Getting started
===============
Note: This installation procedure assumes that you are running the [Ubuntu](http://www.ubuntu.com/) operating system.

The installation of OpenTidalFarm depends on [FEniCS project](http://fenicsproject.org/download/) and [dolfin-adjoint](http://dolfin-adjoint.org/download/index.html)
which need to be downloaded first. 

Next, you can [download OpenTidalFarm](https://github.com/funsim/OpenTidalFarm/zipball/master) and extract it.
Open a terminal and change into the extracted directory.
Then run

`source export_path.sh`

to include the required libraries to you system path.

Now you are ready to run one of the many examples in the examples/ folder.

Contact 
=======
<a id="contact"> </a>
For questions and support please contact Simon W. Funke <s.funke09@imperial.ac.uk>.


Licence
=======
The OpenTidalFarm is an open source project that can be freely used under the 
[GNU GPL version 3](http://www.gnu.org/licenses/gpl.html)
licence.
