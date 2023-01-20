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

#include <vector> // std::vector
#include <map> // std::map
#include <sstream> // std::ostringstream

namespace Math {

class SetBase {
  public:
    SetBase();
    const bool& get_is_empty() const;
    void set_is_empty(bool val);
  protected:
    bool m_is_empty;
    void throw_string_if_is_empty() const;
}; // class SetBase

/* @brief https://en.wikipedia.org/wiki/Interval_(mathematics)
 *        An empty set is considered an interval, hence the inheritance from SetBase
 *        https://math.stackexchange.com/questions/1228307/why-is-the-empty-set-considered-an-interval
 ******************************************************************************/
template<class T>
class Interval : public SetBase {
  public:
    Interval();
    Interval(T min, T max);
    /*! @param[in] min               Minimum value for interval.
     *  @param[in] max               Maximum value for interval.
     *  @param[in] fp_comparison_tol Tolerance used for determining equality in
     *                               this event that this interval's min/max
     *                               values are compared against other values.
     *                               Value should be > 0 and only set set for
     *                               floating point template types.
     **************************************************************************/
    Interval(T min, T max, T fp_comparison_tol);
    Interval(const Interval<int32_t>& obj);
    bool operator==(const Interval<T>& rhs) const;
    const T& get_min() const;
    const T& get_max() const;
    bool get_is_fp() const;
    T    get_fp_comparison_tol() const;
    void set_min(T min);
    void set_max(T max);
    //@{ /// @brief https://en.wikipedia.org/wiki/Subset
    bool is_superset_of(T val) const;
    bool is_superset_of(const Interval<T>& interval) const;
    bool is_proper_superset_of(T val) const;
    bool is_proper_superset_of(const Interval<T>& interval) const;
    //@}
  protected:
    T    m_min;
    T    m_max;
    /// @brief Indicates template type is floating point.
    bool m_is_fp;
    /// @brief Comparison tolerance when using floating point template type.
    T    m_fp_comparison_tol;
    void throw_invalid_argument_if_max_gt_min() const;
}; // class Interval

/*! @brief <B>Exception safety: If min <= max, No-throw guarantee.
 *                              If min > max, Strong guarantee.</B>
 ******************************************************************************/
template<>
Interval<float>::Interval(float min, float max, float fp_comparison_tol) :
    SetBase(), m_min(min), m_max(max), m_is_fp(true),
    m_fp_comparison_tol(fp_comparison_tol) {

  if(m_fp_comparison_tol <= 0) {
    std::ostringstream oss;
    oss << "Interval object constructed with invalid tolerance comparison ";
    oss << "value of " << m_fp_comparison_tol;
    throw std::invalid_argument(oss.str());
  }

  m_is_empty = false;
  throw_invalid_argument_if_max_gt_min();
}

/*! @brief <B>Exception safety: If min <= max, No-throw guarantee.
 *                              If min > max, Strong guarantee.</B>
 ******************************************************************************/
template<>
Interval<double>::Interval(double min, double max, double fp_comparison_tol) :
    SetBase(), m_min(min), m_max(max), m_is_fp(true),
    m_fp_comparison_tol(fp_comparison_tol) {

  if(m_fp_comparison_tol <= 0) {
    std::ostringstream oss;
    oss << "Interval object constructed with invalid tolerance comparison ";
    oss << "value of " << m_fp_comparison_tol;
    throw std::invalid_argument(oss.str());
  }
  m_is_empty = false;
  throw_invalid_argument_if_max_gt_min();
}

/// @brief https://en.wikipedia.org/wiki/Set_(mathematics)
template<class T>
class Set : public SetBase {
  public:
    Set();
    Set(const Interval<T>& interval);
    Set(const std::vector<Interval<T> >& intervals);
    const std::vector<Interval<T> >& get_intervals() const;
    T get_min() const;
    T get_max() const;
    bool operator==(const Set<T>& rhs) const;
    bool operator!=(const Set<T>& rhs) const;
  protected:
    std::vector<Interval<T> > m_intervals;
}; // class Set

/*! @brief Constraint Satisfaction Problem Solver.
 *         (https://en.wikipedia.org/wiki/Constraint_satisfaction_problem)
 ******************************************************************************/
class CSPSolver {
  protected:
    struct CondConstr {
      /// @brief name of var conditionally constrained
      const char* m_v;
      /// @brief name of var for the condition
      const char* m_cv;
    };
  public:
    /// @brief represents a function
    template<class T> struct Func {
      const char* m_lhs;
      const char* m_type;
      T           m_rhs;
      Func(const char* lhs, const char* type, T rhs) :
          m_lhs(lhs), m_type(type), m_rhs(rhs) {
      }
    };
    /// @brief Constraint.
    struct Constr : public Func<const char*> {
      //public:
        /* @brief A condition is represented as a (condition-less) constraint, as
         *        a constraint is already conveniently represented by an equality
         *        function, which is preciely how conditions are specified.
         **********************************************************************/
        typedef Constr Cond;
        Constr(const char* lhs, const char* type, const int32_t rhs,
            int32_t idx_cond = 0);
        Constr(const char* lhs, const char* type, const double rhs,
            int32_t idx_cond = 0);
        Constr(const char* lhs, const char* type, const char* rhs,
            int32_t idx_cond = 0);
        Constr(const char* lhs, const char* type, Func* rhs,
            int32_t idx_cond = 0);
        bool operator==(const Constr& rhs) const;
      //protected:
        typedef Func<const char*> Func;
        /// @brief left hand side variable name
        int32_t    m_rhs_int32_const; /// @TODO make const?
        double     m_rhs_double_const; /// @TODO make const?
        /// @brief right hand side variable name
        Func*      m_rhs_func;
        bool       m_rhs_is_var; /// @TODO make const
        bool       m_rhs_is_int32_const; /// @TODO make const?
        bool       m_rhs_is_double_const; /// @TODO make const?
        bool       m_rhs_is_func; /// @TODO make const?
        /// @brief Will be null if constraint has no condition.
        //Cond*      m_p_cond; /// @TODO make const?
        int32_t    m_idx_cond; /// @TODO make const?
        /* @brief Indicates constraint is to be applied for the "otherwise"
         * condition in an if .. if .. otherwise scenario. Overrides m_p_cond.
         **********************************************************************/
        bool m_cond_is_otherwise;
        Constr(bool cond_is_otherwise = false);
        void throw_invalid_argument_if_constraint_not_supported();
    }; // struct Constr
    struct OtherwiseCond : public Constr {
      public:
      OtherwiseCond();
    }; // struct OtherwiseCond
    /*! @brief A constraint's condition is formulated the same as a
     *         condition-less constraint.
     ************************************************************************/
    //typedef Constr Cond;
    /// @brief https://en.wikipedia.org/wiki/Feasible_region
    struct FeasibleRegionLimits {
      struct Var {
        Set<int32_t> m_int32_set;
        Set<double>  m_double_set;
        double       m_fp_comparison_tol;
        const bool   m_type_is_int32;
        const bool   m_type_is_double;
        Var(int32_t min, int32_t max) :
            m_int32_set(Interval<int32_t>(min, max)),
            m_double_set(),
            m_fp_comparison_tol(0.),
            m_type_is_int32(true), m_type_is_double(false) {
        }
        Var(double min, double max, double fp_comparison_tol) :
            m_int32_set(),
            m_double_set(Interval<double>(min, max, fp_comparison_tol)),
            m_fp_comparison_tol(fp_comparison_tol),
            m_type_is_int32(false), m_type_is_double(true) {
        }
        bool contains(Interval<int32_t> interval);
        bool contains(Interval<double> interval);
        bool get_is_empty();
      }; // struct Var
      typedef std::map<const char*, Var> VarMap;
      VarMap m_vars;
      Interval<int32_t> get_int32_interval_limits();
      Interval<double> get_double_interval_limits(double tol);
      void set_var_limits_to_type_limits(
          std::pair<const char* const, FeasibleRegionLimits::Var>& var);
      void set_var_limits_to_empty_set(
          std::pair<const char* const, FeasibleRegionLimits::Var>& var);
      bool operator==(const FeasibleRegionLimits& rhs) const;
      bool operator!=(const FeasibleRegionLimits& rhs) const;
    }; // struct FeasibleRegionLimits
    /// @brief Available variable domains (D in CSP <X,D,C>)
    /*enum class domain_t {int32};*/
    CSPSolver(size_t max_num_constr_prop_loop_iter = 1024);
    /// @brief Add integer variable in given domain (X in given D for CSP <X,D,C>)
    template<typename T> void add_var(const char* var_key);
    /*! @brief Add floating point variable in given domain (X in given D for CSP <X,D,C>)
     *  @param[in] var_key           C-string key which will be used to refer to
     *  @param[in] fp_comparison_tol Tolerance used for determining equality in
     *                               this event that this variable's
     *                               values are compared against other values.
     *                               Value should be > 0 and only set set for
     *                               floating point template types.
     **************************************************************************/
    template<typename T> void add_var(const char* var_key, T fp_comparison_tol);
    /*! @brief Constrain variable. Left-hand side of equation
     *         contains only the variable being constrained, e.g.
     *         e.g. x1 >= 5 if x2 > 9 would
     *         be implemented as add_constr("x1", ">=", 5, Constr("x2", ">", 9).
     m  @param[in] type One of: ">=" ">" "<=" "<" "="
     **************************************************************************/
    template<typename T> Constr& add_constr(
        const char* lhs, const char* type, const T rhs);
    /*! @brief Conditionally constrain variable. Left-hand side of equation
     *         contains only the variable being constrained, e.g.
     *         e.g. x1 >= 5 if x2 > 9 would
     *         be implemented as add_constr("x1", ">=", 5, Constr("x2", ">", 9).
     m  @param[in] type One of: ">=" ">" "<=" "<" "="
     **************************************************************************/
    template<typename T> Constr& add_constr(
        const char* lhs, const char* type, const T rhs,
        const Constr::Cond& cond);
    void remove_constr(const Constr& contr);
    const std::vector<Constr>& get_constr() const;
    /// @brief https://en.wikipedia.org/wiki/Feasible_region
    const FeasibleRegionLimits& get_feasible_region_limits() const;
    bool feasible_region_limits_is_empty_for_var(const char* var_key) const;
    /// get limits for feasible region for one variable in particular
    const FeasibleRegionLimits::Var& get_feasible_region_limits(
        const char* var) const;
    double get_feasible_region_limits_min_double(
        const char* var) const;
    bool get_var_has_been_added(const char* var_key) const;
    template<typename T> bool val_is_within_var_feasible_region(T val,
        const char* var_key) const;
  protected:
    size_t                    m_max_num_constr_prop_loop_iter;
    std::vector<Constr>       m_constr;
    std::vector<Constr::Cond> m_cond;
    FeasibleRegionLimits m_feasible_region_limits;

    Interval<int32_t> get_interval_for_constr(Constr constr);
    Interval<double> get_interval_for_constr(Constr constr, double tol);
    void dilate(std::pair<const char* const, FeasibleRegionLimits::Var>& var,
        Interval<int32_t>& iv);
    void dilate(std::pair<const char* const, FeasibleRegionLimits::Var>& var,
        Interval<double>& iv);
    void erode(std::pair<const char* const, FeasibleRegionLimits::Var>& var,
        Interval<int32_t>& iv);
    void erode(std::pair<const char* const, FeasibleRegionLimits::Var>& var,
        Interval<double>& iv);
    void propagate_constr_rhs_const(
        std::pair<const char* const, FeasibleRegionLimits::Var>& ivar,
        Constr& constr, /*const std::vector<CSPSolver::CondConstr>& cc*/
        bool do_dilate);
    void propagate_constr_rhs_var(
        std::pair<const char* const, FeasibleRegionLimits::Var>& ivar,
        Constr& constr, /*const std::vector<CSPSolver::CondConstr>& cc*/
        bool do_dilate);
    /// @return vector of names for variables (X) constrained conditionally
    std::vector<CondConstr> find_cond_constr();
    void assign_set_to_domain_limits(Set<int32_t>& set, int32_t tol);
    void assign_set_to_domain_limits(Set<double>& set, double tol);
    void set_var_limits_to_empty_set(
        std::pair<const char* const, FeasibleRegionLimits::Var>& ivar);
    std::vector<CondConstr> find_cond_constrs();
    /// @brief (https://en.wikipedia.org/wiki/Constr_propagation)
    void propagate_constraints();
    void throw_invalid_argument_if_var_key_has_not_been_added(
        const char* var_key);
}; // class CSPSolver

} // namespace Math

#include "Math.cc"

#endif // _MATH_HH
