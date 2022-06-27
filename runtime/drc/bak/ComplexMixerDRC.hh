/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of OpenCPI <http://www.opencpi.org>
 *
 * OpenCPI is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option) any
 * later version.
 *
 * OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
 * details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _COMPLEX_MIXER_DRC_HH
#define _COMPLEX_MIXER_DRC_HH

namespace DRC {

// -----------------------------------------------------------------------------
// STEP 1 - IF IS_LOCKING SUPPORTED,
//          DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class CICIntCSP : public CSPBase {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief for the cic_int,
   *        define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_x_d_cic_int() {
    m_solver.add_var<double>("r", dfp_tol);
    m_solver.add_var<double>("cic_int_fc_meghz_xin", dfp_tol);
    m_solver.add_var<double>("cic_int_fc_meghz_xout", dfp_tol);
    m_solver.add_var<double>("cic_int_bw_meghz_xin", dfp_tol);
    m_solver.add_var<double>("cic_int_bw_meghz_xout", dfp_tol);
    m_solver.add_var<double>("cic_int_fs_megsps_xin", dfp_tol);
    m_solver.add_var<double>("cic_int_fs_megsps_xout", dfp_tol);
  }
  /* @brief for the cic_int,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_c_cic_int() {
    m_solver.add_constr("r", "<=", -65536.);
    m_solver.add_constr("r", ">=", 65535.);
    m_solver.add_constr("cic_int_fc_meghz_xout", "=", "cic_int_fc_meghz_xin");
    /// @TODO add commented out functionality
    /*Func f1("cic_int_bw_meghz_xin", "*", "r");
    m_solver.add_constr("cic_int_bw_meghz_xout", "=", &ff);
    Func f2("cic_int_fs_megsps_xin", "*","r");
    m_solver.add_constr("cic_int_fs_megsps_xout", "=", &ff);*/
  }
  public:
  CICIntCSP() : CSPBase() {
    define();
    //std::cout << "[INFO] " << get_feasible_region_limits() << "\n";
  }
  /* @brief instance cic_int
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  void instance_cic_int() {
    define_x_d_cic_int();
    define_c_cic_int();
  }
  /// @brief define Constraint Satisfaction Problem (CSP)
  void define() {
    instance_cic_int();
  }
}; // class CICIntCSP
#endif

} // namespace DRC

#endif // _COMPLEX_MIXER_DRC_HH
