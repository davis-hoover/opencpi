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

#ifndef _CIC_INT_DRC_HH
#define _CIC_INT_DRC_HH

#include "DRC.hh"

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
    m_solver.add_var<double>("phs_inc_divided", dfp_tol);
    m_solver.add_var<int32_t>("nco_output_freq");
    m_solver.add_var<int32_t>("cic_int_dir_xout");
    m_solver.add_var<int32_t>("cic_int_dir_xin");
    m_solver.add_var<double>("cic_int_fc_meghz_xin", dfp_tol);
    m_solver.add_var<double>("cic_int_fc_meghz_xout", dfp_tol);
    m_solver.add_var<double>("cic_int_bw_meghz_xin", dfp_tol);
    m_solver.add_var<double>("cic_int_bw_meghz_xout", dfp_tol);
    m_solver.add_var<double>("cic_int_fs_megsps_xin", dfp_tol);
    m_solver.add_var<double>("cic_int_fs_megsps_xout", dfp_tol);
    m_solver.add_var<int32_t>("cic_int_samps_comp_xin");
    m_solver.add_var<int32_t>("cic_int_samps_comp_xout");
    m_solver.add_var<int32_t>("cic_int_gain_mode_xin");
    m_solver.add_var<int32_t>("cic_int_gain_mode_xout");
    m_solver.add_var<double>("cic_int_gain_db_xin", dfp_tol);
    m_solver.add_var<double>("cic_int_gain_db_xout", dfp_tol);
  }
  /* @brief for the cic_int,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_c_cic_int() {
    m_solver.add_constr("cic_int_dir_xout", "=", "cic_int_dir_xin");
    /// @TODO add commented out functionality
    /*m_solver.add_constr("phs_inc_divided", ">=", -32768./65536.);
    m_solver.add_constr("phs_inc_divided", "<=", 32767./65536.);
    Func f1("cic_int_fs_megsps_xin", "x", "phs_inc_divided");
    m_solver.add_constr("nco_output_freq", "=", &f1);
    Func f2("cic_int_fc_meghz_xin", "+", "nco_output_freq");
    m_solver.add_constr("cic_int_fc_meghz_xout", "=", &f2);*/
    m_solver.add_constr("cic_int_bw_meghz_xout", "=", "cic_int_bw_meghz_xin");
    m_solver.add_constr("cic_int_fs_megsps_xout", "=", "cic_int_fs_megsps_xin");
    m_solver.add_constr("cic_int_fs_megsps_xout", "=", "cic_int_fs_megsps_xin");
    m_solver.add_constr("cic_int_samps_comp_xout", "=", "cic_int_samps_comp_xout");
    m_solver.add_constr("cic_int_gain_mode_xout", "=", "cic_int_gain_mode_xin");
    m_solver.add_constr("cic_int_gain_db_xout", "=", "cic_int_gain_db_xin");
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

#endif // _CIC_INT_DRC_HH
