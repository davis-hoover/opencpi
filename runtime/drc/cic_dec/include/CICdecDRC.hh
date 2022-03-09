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

#ifndef _CIC_DEC_DRC_HH
#define _CIC_DEC_DRC_HH

namespace DRC {

// -----------------------------------------------------------------------------
// STEP 1 - IF IS_LOCKING SUPPORTED,
//          DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class cic_decCSP : public CSPBase {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief for the cic_dec,
   *        define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_x_d_cic_dec() {
    m_solver.add_var<int32_t>("r");
    m_solver.add_var<double>("cic_dec_fc_meghz_xin", dfp_tol);
    m_solver.add_var<double>("cic_dec_fc_meghz_xout", dfp_tol);
    m_solver.add_var<double>("cic_dec_bw_meghz_xin", dfp_tol);
    m_solver.add_var<double>("cic_dec_bw_meghz_xout", dfp_tol);
    m_solver.add_var<double>("cic_dec_fs_megsps_xin", dfp_tol);
    m_solver.add_var<double>("cic_dec_fs_megsps_xout", dfp_tol);
  }
  /* @brief for the cic_dec,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_c_cic_dec() {
    m_solver.add_constr("r", ">=", "4");
    m_solver.add_constr("r", "<=", "8192");
    m_solver.add_constr("cic_dec_fc_meghz_xout", "=", "cic_dec_fc_meghz_xin");
    m_solver.add_constr("cic_dec_bw_meghz_xout", "=", "cic_dec_bw_meghz_xin");
    m_solver.add_constr("cic_dec_fs_meghz_xout", "=", "cic_dec_fs_meghz_xin");
  }
  public:
  cic_decCSP() : CSPBase() {
    define();
    //std::cout << "[INFO] " << get_feasible_region_limits() << "\n";
  }
  /* @brief instance cic_dec
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  void instance_cic_dec() {
    define_x_d_cic_dec();
    define_c_cic_dec();
  }
  /// @brief define Constraint Satisfaction Problem (CSP)
  void define() {
    instance_cic_dec();
  }
}; // class cic_decCSP
#endif

} // namespace DRC

#endif // _CIC_DEC_DRC_HH
