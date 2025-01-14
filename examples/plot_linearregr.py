r"""
Linear Regression
=================

This example shows how to use the :py:class:`pylops.LinearRegression` operator
to perform *Linear regression analysis*.

In short, linear regression is the problem of finding the best fitting
coefficients, namely intercept :math:`\mathbf{x_0}` and gradient
:math:`\mathbf{x_1}`, for this equation:

    .. math::
        y_i = x_0 + x_1 t_i   \qquad \forall i=0,1,\ldots,N-1

As we can express this problem in a matrix form:

    .. math::
        \mathbf{y}=  \mathbf{A} \mathbf{x}

our solution can be obtained by solving the following optimization problem:

    .. math::
        J= \|\mathbf{y} - \mathbf{A} \mathbf{x}\|_2

See documentation of :py:class:`pylops.LinearRegression` for more detailed
definition of the forward problem.
"""
import matplotlib.pyplot as plt
import numpy as np

import pylops

plt.close("all")
np.random.seed(10)

###############################################################################
# Define the input parameters: number of samples along the t-axis (``N``),
# linear regression coefficients (``x``), and standard deviation of noise
# to be added to data (``sigma``).
N = 30
x = np.array([1.0, 2.0])
sigma = 1

###############################################################################
# Let's create the time axis and initialize the
# :py:class:`pylops.LinearRegression` operator
t = np.arange(N, dtype="float64")
LRop = pylops.LinearRegression(t, dtype="float64")

###############################################################################
# We can then apply the operator in forward mode to compute our data points
# along the x-axis (``y``). We will also generate some random gaussian noise
# and create a noisy version of the data (``yn``).
y = LRop * x
yn = y + np.random.normal(0, sigma, N)

###############################################################################
# We are now ready to solve our problem. As we are using an operator from the
# :py:class:`pylops.LinearOperator` family, we can simply use ``/``,
# which in this case will solve the system by means of an iterative solver
# (i.e., :py:func:`scipy.sparse.linalg.lsqr`).
xest = LRop / y
xnest = LRop / yn

###############################################################################
# Let's plot the best fitting line for the case of noise free and noisy data
plt.figure(figsize=(5, 7))
plt.plot(
    np.array([t.min(), t.max()]),
    np.array([t.min(), t.max()]) * x[1] + x[0],
    "k",
    lw=4,
    label=rf"true: $x_0$ = {x[0]:.2f}, $x_1$ = {x[1]:.2f}",
)
plt.plot(
    np.array([t.min(), t.max()]),
    np.array([t.min(), t.max()]) * xest[1] + xest[0],
    "--r",
    lw=4,
    label=rf"est noise-free: $x_0$ = {xest[0]:.2f}, $x_1$ = {xest[1]:.2f}",
)
plt.plot(
    np.array([t.min(), t.max()]),
    np.array([t.min(), t.max()]) * xnest[1] + xnest[0],
    "--g",
    lw=4,
    label=rf"est noisy: $x_0$ = {xnest[0]:.2f}, $x_1$ = {xnest[1]:.2f}",
)
plt.scatter(t, y, c="r", s=70)
plt.scatter(t, yn, c="g", s=70)
plt.legend()
plt.tight_layout()

###############################################################################
# Once that we have estimated the best fitting coefficients :math:`\mathbf{x}`
# we can now use them to compute the *y values* for a different set of values
# along the *t-axis*.
t1 = np.linspace(-N, N, 2 * N, dtype="float64")
y1 = LRop.apply(t1, xest)

plt.figure(figsize=(5, 7))
plt.plot(t, y, "k", label="Original axis")
plt.plot(t1, y1, "r", label="New axis")
plt.scatter(t, y, c="k", s=70)
plt.scatter(t1, y1, c="r", s=40)
plt.legend()
plt.tight_layout()


###############################################################################
# We consider now the case where some of the observations have large errors.
# Such elements are generally referred to as *outliers* and can affect the
# quality of the least-squares solution if not treated with care. In this
# example we will see how using a L1 solver such as
# :py:func:`pylops.optimization.sparsity.IRLS` can drammatically improve the
# quality of the estimation of intercept and gradient.


class CallbackIRLS(pylops.optimization.callback.Callbacks):
    def __init__(self, n):
        self.n = n
        self.xirls_hist = []
        self.rw_hist = []

    def on_step_end(self, solver, x):
        print(solver.iiter)
        if solver.iiter > 1:
            self.xirls_hist.append(x)
            self.rw_hist.append(solver.rw)
        else:
            self.rw_hist.append(np.ones(self.n))


# Add outliers
yn[1] += 40
yn[N - 2] -= 20

# IRLS
nouter = 20
epsR = 1e-2
epsI = 0
tolIRLS = 1e-2

xnest = LRop / yn

cb = CallbackIRLS(N)
irlssolve = pylops.optimization.sparsity.IRLS(
    LRop,
    [
        cb,
    ],
)
xirls, nouter = irlssolve.solve(
    yn, nouter=nouter, threshR=False, epsR=epsR, epsI=epsI, tolIRLS=tolIRLS
)
xirls_hist, rw_hist = np.array(cb.xirls_hist), cb.rw_hist
print(f"IRLS converged at {nouter} iterations...")

plt.figure(figsize=(5, 7))
plt.plot(
    np.array([t.min(), t.max()]),
    np.array([t.min(), t.max()]) * x[1] + x[0],
    "k",
    lw=4,
    label=rf"true: $x_0$ = {x[0]:.2f}, $x_1$ = {x[1]:.2f}",
)
plt.plot(
    np.array([t.min(), t.max()]),
    np.array([t.min(), t.max()]) * xnest[1] + xnest[0],
    "--r",
    lw=4,
    label=rf"L2: $x_0$ = {xnest[0]:.2f}, $x_1$ = {xnest[1]:.2f}",
)
plt.plot(
    np.array([t.min(), t.max()]),
    np.array([t.min(), t.max()]) * xirls[1] + xirls[0],
    "--g",
    lw=4,
    label=rf"L1 - IRSL: $x_0$ = {xirls[0]:.2f}, $x_1$ = {xirls[1]:.2f}",
)
plt.scatter(t, y, c="r", s=70)
plt.scatter(t, yn, c="g", s=70)
plt.legend()
plt.tight_layout()

###############################################################################
# Let's finally take a look at the convergence of IRLS. First we visualize
# the evolution of intercept and gradient

fig, axs = plt.subplots(2, 1, figsize=(8, 10))
fig.suptitle("IRLS evolution", fontsize=14, fontweight="bold", y=0.95)
axs[0].plot(xirls_hist[:, 0], xirls_hist[:, 1], ".-k", lw=2, ms=20)
axs[0].scatter(x[0], x[1], c="r", s=70)
axs[0].set_title("Intercept and gradient")
axs[0].grid()
for iiter in range(nouter):
    axs[1].semilogy(
        rw_hist[iiter],
        color=(iiter / nouter, iiter / nouter, iiter / nouter),
        label="iter%d" % iiter,
    )
axs[1].set_title("Weights")
axs[1].legend(loc=5, fontsize="small")
plt.tight_layout()
plt.subplots_adjust(top=0.8)
