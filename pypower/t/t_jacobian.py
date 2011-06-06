# Copyright (C) 2004-2011 Power System Engineering Research Center
# Copyright (C) 2010-2011 Richard Lincoln
#
# PYPOWER is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# PYPOWER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY], without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PYPOWER. If not, see <http://www.gnu.org/licenses/>.

from numpy import ones, conj, eye, exp, pi

from pypower.case30 import case30
from pypower.ppoption import ppoption
from pypower.loadcase import loadcase
from pypower.ext2int import ext2int1
from pypower.runpf import runpf
from pypower.makeYbus import makeYbus
from pypower.dSbus_dV import dSbus_dV
from pypower.dSbr_dV import dSbr_dV
from pypower.dAbr_dV import dAbr_dV
from pypower.dIbr_dV import dIbr_dV

from pypower.idx_bus import VM, VA
from pypower.idx_brch import F_BUS, T_BUS

from pypower.t.t_begin import t_begin
from pypower.t.t_end import t_end
from pypower.t.t_is import t_is


def t_jacobian(quiet=False):
    """Numerical tests of partial derivative code.

    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    t_begin(28, quiet)

    ## run powerflow to get solved case
    opt = ppoption
    opt['VERBOSE'] = 0
    opt['OUT_ALL'] = 0
    ppc = loadcase(case30())

    results, _ = runpf(ppc, opt)
    baseMVA, bus, gen, branch = \
        results['baseMVA'], results['bus'], results['gen'], results['branch']

    ## switch to internal bus numbering and build admittance matrices
    _, bus, gen, branch = ext2int1(bus, gen, branch)
    Ybus, Yf, Yt = makeYbus(baseMVA, bus, branch)
    Ybus_full = Ybus.todense()
    Yf_full   = Yf.todense()
    Yt_full   = Yt.todense()
    Vm = bus[:, VM].copy()
    Va = bus[:, VA] * (pi / 180)
    V = Vm * exp(1j * Va)
    f = branch[:, F_BUS].astype(int)       ## list of "from" buses
    t = branch[:, T_BUS].astype(int)       ## list of "to" buses
    nl = len(f)
    nb = len(V)
    pert = 1e-8

    ##-----  check dSbus_dV code  -----
    ## full matrices
    dSbus_dVm_full, dSbus_dVa_full = dSbus_dV(Ybus_full, V)

    ## sparse matrices
    dSbus_dVm, dSbus_dVa = dSbus_dV(Ybus, V)
    dSbus_dVm_sp = dSbus_dVm.todense()
    dSbus_dVa_sp = dSbus_dVa.todense()

    ## compute numerically to compare
    Vmp = (Vm * ones((1, nb)) + pert*eye(nb)) * (exp(1j * Va) * ones((1, nb)))
    Vap = (Vm * ones((1, nb))) * (exp(1j * (Va*ones((1, nb)) + pert*eye(nb))))
    num_dSbus_dVm = (Vmp * conj(Ybus * Vmp) - V * ones(nb) * conj(Ybus * V * ones((1, nb)))) / pert
    num_dSbus_dVa = (Vap * conj(Ybus * Vap) - V * ones(nb) * conj(Ybus * V * ones((1, nb)))) / pert

    t_is(dSbus_dVm_sp, num_dSbus_dVm, 5, 'dSbus_dVm (sparse)')
    t_is(dSbus_dVa_sp, num_dSbus_dVa, 5, 'dSbus_dVa (sparse)')
    t_is(dSbus_dVm_full, num_dSbus_dVm, 5, 'dSbus_dVm (full)')
    t_is(dSbus_dVa_full, num_dSbus_dVa, 5, 'dSbus_dVa (full)')

    ##-----  check dSbr_dV code  -----
    ## full matrices
    dSf_dVa_full, dSf_dVm_full, dSt_dVa_full, dSt_dVm_full, _, _ = \
            dSbr_dV(branch, Yf_full, Yt_full, V)

    ## sparse matrices
    dSf_dVa, dSf_dVm, dSt_dVa, dSt_dVm, Sf, St = dSbr_dV(branch, Yf, Yt, V)
    dSf_dVa_sp = dSf_dVa.todense()
    dSf_dVm_sp = dSf_dVm.todense()
    dSt_dVa_sp = dSt_dVa.todense()
    dSt_dVm_sp = dSt_dVm.todense()

    ## compute numerically to compare
    Vmpf = Vmp[f, :]
    Vapf = Vap[f, :]
    Vmpt = Vmp[t, :]
    Vapt = Vap[t, :]
    Sf2 = (V[f] * ones(nb)) * conj(Yf * V * ones(nb))
    St2 = (V[t] * ones(nb)) * conj(Yt * V * ones(nb))
    Smpf = Vmpf * conj(Yf * Vmp)
    Sapf = Vapf * conj(Yf * Vap)
    Smpt = Vmpt * conj(Yt * Vmp)
    Sapt = Vapt * conj(Yt * Vap)

    num_dSf_dVm = ( (Smpf - Sf2) / pert ).todense()
    num_dSf_dVa = ( (Sapf - Sf2) / pert ).todense()
    num_dSt_dVm = ( (Smpt - St2) / pert ).todense()
    num_dSt_dVa = ( (Sapt - St2) / pert ).todense()

    t_is(dSf_dVm_sp, num_dSf_dVm, 5, 'dSf_dVm (sparse)')
    t_is(dSf_dVa_sp, num_dSf_dVa, 5, 'dSf_dVa (sparse)')
    t_is(dSt_dVm_sp, num_dSt_dVm, 5, 'dSt_dVm (sparse)')
    t_is(dSt_dVa_sp, num_dSt_dVa, 5, 'dSt_dVa (sparse)')
    t_is(dSf_dVm_full, num_dSf_dVm, 5, 'dSf_dVm (full)')
    t_is(dSf_dVa_full, num_dSf_dVa, 5, 'dSf_dVa (full)')
    t_is(dSt_dVm_full, num_dSt_dVm, 5, 'dSt_dVm (full)')
    t_is(dSt_dVa_full, num_dSt_dVa, 5, 'dSt_dVa (full)')

    ##-----  check dAbr_dV code  -----
    ## full matrices
    dAf_dVa_full, dAf_dVm_full, dAt_dVa_full, dAt_dVm_full = \
        dAbr_dV(dSf_dVa_full, dSf_dVm_full, dSt_dVa_full, dSt_dVm_full, Sf, St)
    ## sparse matrices
    dAf_dVa, dAf_dVm, dAt_dVa, dAt_dVm = \
                            dAbr_dV(dSf_dVa, dSf_dVm, dSt_dVa, dSt_dVm, Sf, St)
    dAf_dVa_sp = dAf_dVa.todense()
    dAf_dVm_sp = dAf_dVm.todense()
    dAt_dVa_sp = dAt_dVa.todense()
    dAt_dVm_sp = dAt_dVm.todense()

    ## compute numerically to compare
    num_dAf_dVm = ( (abs(Smpf)**2 - abs(Sf2)**2) / pert ).todense()
    num_dAf_dVa = ( (abs(Sapf)**2 - abs(Sf2)**2) / pert ).todense()
    num_dAt_dVm = ( (abs(Smpt)**2 - abs(St2)**2) / pert ).todense()
    num_dAt_dVa = ( (abs(Sapt)**2 - abs(St2)**2) / pert ).todense()

    t_is(dAf_dVm_sp, num_dAf_dVm, 4, 'dAf_dVm (sparse)')
    t_is(dAf_dVa_sp, num_dAf_dVa, 4, 'dAf_dVa (sparse)')
    t_is(dAt_dVm_sp, num_dAt_dVm, 4, 'dAt_dVm (sparse)')
    t_is(dAt_dVa_sp, num_dAt_dVa, 4, 'dAt_dVa (sparse)')
    t_is(dAf_dVm_full, num_dAf_dVm, 4, 'dAf_dVm (full)')
    t_is(dAf_dVa_full, num_dAf_dVa, 4, 'dAf_dVa (full)')
    t_is(dAt_dVm_full, num_dAt_dVm, 4, 'dAt_dVm (full)')
    t_is(dAt_dVa_full, num_dAt_dVa, 4, 'dAt_dVa (full)')

    ##-----  check dIbr_dV code  -----
    ## full matrices
    dIf_dVa_full, dIf_dVm_full, dIt_dVa_full, dIt_dVm_full, If, It = \
            dIbr_dV(branch, Yf_full, Yt_full, V)

    ## sparse matrices
    dIf_dVa, dIf_dVm, dIt_dVa, dIt_dVm, If, It = dIbr_dV(branch, Yf, Yt, V)
    dIf_dVa_sp = dIf_dVa.todense()
    dIf_dVm_sp = dIf_dVm.todense()
    dIt_dVa_sp = dIt_dVa.todense()
    dIt_dVm_sp = dIt_dVm.todense()

    ## compute numerically to compare
    num_dIf_dVm = ( (Yf * Vmp - Yf * V * ones(nb)) / pert ).todense()
    num_dIf_dVa = ( (Yf * Vap - Yf * V * ones(nb)) / pert ).todense()
    num_dIt_dVm = ( (Yt * Vmp - Yt * V * ones(nb)) / pert ).todense()
    num_dIt_dVa = ( (Yt * Vap - Yt * V * ones(nb)) / pert ).todense()

    t_is(dIf_dVm_sp, num_dIf_dVm, 5, 'dIf_dVm (sparse)')
    t_is(dIf_dVa_sp, num_dIf_dVa, 5, 'dIf_dVa (sparse)')
    t_is(dIt_dVm_sp, num_dIt_dVm, 5, 'dIt_dVm (sparse)')
    t_is(dIt_dVa_sp, num_dIt_dVa, 5, 'dIt_dVa (sparse)')
    t_is(dIf_dVm_full, num_dIf_dVm, 5, 'dIf_dVm (full)')
    t_is(dIf_dVa_full, num_dIf_dVa, 5, 'dIf_dVa (full)')
    t_is(dIt_dVm_full, num_dIt_dVm, 5, 'dIt_dVm (full)')
    t_is(dIt_dVa_full, num_dIt_dVa, 5, 'dIt_dVa (full)')

    t_end


if __name__ == "__main__":
    t_jacobian(quiet=False)
