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

#ifndef _MATH_HH
#define _MATH_HH

#include <cstdint>
#include <string>
#include <vector> // std::vector
#include <map> // std::map

class SetBase {
  public:
  SetBase();
  const bool& get_is_empty() const;
  void set_is_empty(bool val);
  protected:
  bool m_is_empty;
  void throw_if_is_empty() const;
}; // class SetBase

/* @brief https://en.wikipedia.org/wiki/_Interval_(mathematics)
 *        An empty set is considered an interval, hence the inheritance from
 *        SetBase
 *        https://math.stackexchange.com/questions/1228307/why-is-the-empty-set-considered-an-interval
 * @todo / FIXME remove leading underscore and consolidate
 ******************************************************************************/
template<class T>
class _Interval : public SetBase {
  public:
  _Interval();
  _Interval(T min, T max);
  /*! @param[in] min               Minimum value for interval.
   *  @param[in] max               Maximum value for interval.
   *  @param[in] fp_comparison_tol Tolerance used for determining equality in
   *                               this event that this interval's min/max
   *                               values are compared against other values.
   *                               Value should be > 0 and only set set for
   *                               floating point template types.
   **************************************************************************/
  _Interval(T min, T max, T fp_comparison_tol);
  _Interval(const _Interval<int32_t>& obj);
  bool operator==(const _Interval<T>& rhs) const;
  const T& get_min() const;
  const T& get_max() const;
  bool get_is_fp() const;
  T    get_fp_comparison_tol() const;
  void set_min(T min);
  void set_max(T max);
  //@{ /// @brief https://en.wikipedia.org/wiki/Subset
  bool is_superset_of(T val) const;
  bool is_superset_of(const _Interval<T>& interval) const;
  bool is_proper_superset_of(T val) const;
  bool is_proper_superset_of(const _Interval<T>& interval) const;
  //@}
  protected:
  T    m_min;
  T    m_max;
  /// @brief Indicates template type is floating point.
  bool m_is_fp;
  /// @brief Comparison tolerance when using floating point template type.
  T    m_fp_comparison_tol;
  void throw_invalid_argument_if_max_gt_min() const;
}; // class _Interval

template<>
_Interval<double>::_Interval(double min, double max, double fp_comparison_tol);

/// @brief https://en.wikipedia.org/wiki/Set_(mathematics)
template<class T>
class Set : public SetBase {
  public:
  Set();
  Set(const _Interval<T>& interval);
  Set(const std::vector<_Interval<T> >& intervals);
  const std::vector<_Interval<T> >& get_intervals() const;
  T get_min() const;
  T get_max() const;
  bool operator==(const Set<T>& rhs) const;
  bool operator!=(const Set<T>& rhs) const;
  protected:
  std::vector<_Interval<T> > m_intervals;
}; // class Set

/*! @brief Constraint Satisfaction Problem Solver.
 *         (https://en.wikipedia.org/wiki/Constraint_satisfaction_problem)
 ******************************************************************************/
class CSPSolver {
  public:
  /// @brief represents a function, e.g. x = 4
  template<class T> struct Func {
    std::string m_lhs; // left-hand side (variable name), e.g. "x"
    std::string m_type; // function type, e.g. "="
    T           m_rhs; // right-hand side, e.g. 4
    Func(const std::string& lhs, const std::string& type, T rhs) :
        m_lhs(lhs), m_type(type), m_rhs(rhs) {
    }
  };
  /// @brief A constraint, which is modelled as a function, e.g. x = 4
  struct Constr : public Func<std::string> {
    //public:
    Constr();
    Constr(const std::string& lhs, const std::string& type, const int32_t rhs);
    Constr(const std::string& lhs, const std::string& type, const double rhs);
    Constr(const std::string& lhs, const std::string& type,
        const std::string& rhs);
    bool operator==(const Constr& rhs) const;
    //protected:
    /// @brief left hand side variable name
    int32_t    m_rhs_int32_const; /// @TODO make const?
    double     m_rhs_double_const; /// @TODO make const?
    bool       m_rhs_is_var; /// @TODO make const
    bool       m_rhs_is_int32_const; /// @TODO make const?
    bool       m_rhs_is_double_const; /// @TODO make const?
    void throw_invalid_argument_if_constraint_not_supported();
  }; // struct Constr
  /// @brief https://en.wikipedia.org/wiki/Feasible_region
  struct FeasibleRegionLimits {
    struct Var {
      Set<int32_t> m_int32_set;
      Set<double>  m_double_set;
      double       m_fp_comparison_tol;
      /// @brief if false, type is double
      const bool   m_type_is_int32;
      Var(int32_t min, int32_t max) :
          m_int32_set(_Interval<int32_t>(min, max)),
          m_double_set(),
          m_fp_comparison_tol(0.),
          m_type_is_int32(true) {
      }
      Var(double min, double max, double fp_comparison_tol) :
          m_int32_set(),
          m_double_set(_Interval<double>(min, max, fp_comparison_tol)),
          m_fp_comparison_tol(fp_comparison_tol),
          m_type_is_int32(false) {
      }
      bool contains(_Interval<int32_t> interval);
      bool contains(_Interval<double> interval);
      bool get_is_empty();
    }; // struct Var
    typedef std::map<std::string, Var> VarMap;
    VarMap m_vars;
    _Interval<int32_t> get_int32_interval_limits();
    _Interval<double> get_double_interval_limits(double tol);
    /// @brief https://en.wikipedia.org/wiki/Universal_set
    void set_var_limits_to_universal_set(
        std::pair<const std::string,FeasibleRegionLimits::Var>& var);
    void set_var_limits_to_empty_set(
        std::pair<const std::string,FeasibleRegionLimits::Var>& var);
    bool operator==(const FeasibleRegionLimits& rhs) const;
    bool operator!=(const FeasibleRegionLimits& rhs) const;
  }; // struct FeasibleRegionLimits
  CSPSolver(size_t max_num_constr_prop_loop_iter = 1024);
  /// @brief Add integer variable in given domain (X in given D for CSP <X,D,C>)
  template<typename T> void add_var(const std::string& var_key);
  /*! @brief Add floating point variable in given domain (X in given D for
   *         CSP <X,D,C>)
   *  @param[in] var_key           C-string key which will be used to refer to
   *  @param[in] fp_comparison_tol Tolerance used for determining equality in
   *                               this event that this variable's
   *                               values are compared against other values.
   *                               Value should be > 0 and only set set for
   *                               floating point template types.
   ****************************************************************************/
  template<typename T> void add_var(const std::string& var_key,
      T fp_comparison_tol);
  /*! @brief Constrain variable. Left-hand side of equation
   *         contains only the variable being constrained, e.g.
   *         e.g. x1 >= 5 if x2 > 9 would
   *         be implemented as add_constr("x1", ">=", 5, Constr("x2", ">", 9).
   m  @param[in] type One of: ">=" ">" "<=" "<" "="
   ****************************************************************************/
  template<typename T> size_t add_constr(
      const std::string& lhs, const std::string& type, const T& rhs);
  void remove_constr(size_t idx);
  const std::map<size_t,Constr>& get_constr() const;
  const CSPSolver::Constr& get_constr(size_t idx) const;
  /// @brief https://en.wikipedia.org/wiki/Feasible_region
  const FeasibleRegionLimits& get_feasible_region_limits() const;
  bool feasible_region_limits_is_empty_for_var(
      const std::string& var_key) const;
  /// @brief get limits for feasible region for one variable in particular
  const FeasibleRegionLimits::Var& get_feasible_region_limits(
      const std::string& var) const;
  double get_feasible_region_limits_min_double(
      const std::string& var) const;
  bool get_var_has_been_added(const std::string& var_key) const;
  template<typename T> bool val_is_within_var_feasible_region(T val,
      const std::string& var_key) const;
  protected:
  size_t                  m_max_num_constr_prop_loop_iter;
  std::map<size_t,Constr> m_constr;
  size_t                  m_constr_max_id;
  FeasibleRegionLimits    m_feasible_region_limits;
  _Interval<int32_t> get_interval_for_constr(Constr constr);
  _Interval<double> get_interval_for_constr(Constr constr, double tol);
  void assign_var_to_intersection_of_var_and_interval(
      std::pair<const std::string,FeasibleRegionLimits::Var>& var,
      _Interval<int32_t>& iv);
  void assign_var_to_intersection_of_var_and_interval(
      std::pair<const std::string,FeasibleRegionLimits::Var>& var,
      _Interval<double>& iv);
  void propagate_constr_rhs_const(
      std::pair<const std::string,FeasibleRegionLimits::Var>& ivar,
      Constr& constr);
  void propagate_constr_rhs_var(
      std::pair<const std::string,FeasibleRegionLimits::Var>& ivar,
      Constr& constr);
  void assign_set_to_universal_set(Set<int32_t>& set, int32_t tol);
  void assign_set_to_universal_set(Set<double>& set, double tol);
  void propagate_constraints();
  void throw_invalid_argument_if_var_key_has_not_been_added(
      const std::string& var_key);
}; // class CSPSolver

#include "Math.cc"

#endif // _MATH_HH
