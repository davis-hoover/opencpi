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

#include <sstream> // std::ostringstream
#include <iostream> // std::ostream
#include <stdexcept> // std::exception, std::invalid_argument
#include <vector> // std::vector
#include <map> // std::map
#include <limits> // std::numeric_limits
#include <utility> // std::make_pair
#include <cmath> // std::abs(double)
#include <algorithm> // std::min
#include <string> // std::string
#include <cfloat> // DBL_MAX
#include <cstring> // strcomp() ///@TODO remove
#include <cassert> /// @TODO/FIXME - remove
#include "Math.hh"

namespace Math {

SetBase::SetBase() : m_is_empty(true) {
}

void
SetBase::throw_string_if_is_empty() const {
  if(m_is_empty) {
    std::ostringstream oss;
    oss << "performed operation on interval min/max of empty interval";
    throw oss.str();
  }
}

/*! @brief <B>Exception safety: No-throw guarantee.</B>
 ******************************************************************************/
const bool&
SetBase::get_is_empty() const {
  return m_is_empty;
}

void
SetBase::set_is_empty(bool val) {
  m_is_empty = val;
}

/*! @brief <B>Exception safety: No-throw guarantee.</B>
 ******************************************************************************/
template<class T>
Interval<T>::Interval() : SetBase(), m_is_fp(false) {
}

/*! @brief <B>Exception safety: If min <= max, No-throw guarantee.
 *                              If min > max, Strong guarantee.</B>
 ******************************************************************************/
template<class T>
Interval<T>::Interval(T min, T max) :
    SetBase(), m_min(min), m_max(max), m_is_fp(false) {
  m_is_empty = false;
  throw_invalid_argument_if_max_gt_min();
}

template<class T>
Interval<T>::Interval(const Interval<int32_t>& obj) :
    SetBase(), m_min(obj.get_min()), m_max(obj.get_max()), m_is_fp(false) {
  m_is_empty = false;
  throw_invalid_argument_if_max_gt_min();
}

template<>
Interval<float>::Interval(float min, float max) : m_min(min), m_max(max) {
  std::ostringstream oss;
  oss << "Interval object constructed for 'float' template type without ";
  oss << "constructor which sets comparison tolerance";
  throw std::invalid_argument(oss.str());
}

/*! @brief <B>Exception safety: Strong guarantee.</B>
 ******************************************************************************/
template<class T>
Interval<T>::Interval(T min, T max, T fp_comparison_tol) :
    SetBase(), m_min(min), m_max(max), m_is_fp(false),
    m_fp_comparison_tol(fp_comparison_tol) {
  std::ostringstream oss;
  oss << "Interval object constructed for non-floating point type but still ";
  oss << "specified comparison tolerance";
  throw std::invalid_argument(oss.str());
}

/*! @brief <B>Exception safety: If min <= max, No-throw guarantee.
 *                              If min > max, Strong guarantee.</B>
 ******************************************************************************/
template<class T> bool
Interval<T>::operator==(const Interval<T>& rhs) const {
  if(m_is_fp != rhs.get_is_fp()) {
    return false;
  }
  if(m_min != rhs.get_min()) {
    return false;
  }
  if(m_max != rhs.get_max()) {
    return false;
  }
  return true;
}

/*! @brief <B>Exception safety: If Interval(float,float,float) was used,
 *                              No-throw guarantee.
 *                              Otherwise, Strong guarantee.</B>
 ******************************************************************************/
template<> bool
Interval<float>::operator==(const Interval<float>& rhs) const {
  if(m_is_fp != rhs.get_is_fp()) {
    return false;
  }
  // m_is_fp is guaranteed to be true by constructor
  if(std::abs(m_min - rhs.get_min()) > m_fp_comparison_tol) {
    return false;
  }
  if(std::abs(m_max - rhs.get_max()) > m_fp_comparison_tol) {
    return false;
  }
  return true;
}

/*! @brief <B>Exception safety: If Interval(double,double,double) was used,
 *                              No-throw guarantee.
 *                              Otherwise, Strong guarantee.</B>
 ******************************************************************************/
template<> bool
Interval<double>::operator==(const Interval<double>& rhs) const {
  if(m_is_fp != rhs.get_is_fp()) {
    return false;
  }
  // m_is_fp is guaranteed to be true by constructor
  if(std::abs(m_min - rhs.get_min()) > m_fp_comparison_tol) {
    return false;
  }
  if(std::abs(m_max - rhs.get_max()) > m_fp_comparison_tol) {
    return false;
  }
  return true;
}

/*! @brief <B>Exception safety: If get_is_empty(), No-throw guarantee.
 *                              Otherwise, Strong guarantee.</B>
 ******************************************************************************/
template<class T> const T&
Interval<T>::get_min() const {
  throw_string_if_is_empty();
  return m_min;
}

/*! @brief <B>Exception safety: If get_is_empty(), No-throw guarantee.
 *                              Otherwise, Strong guarantee.</B>
 ******************************************************************************/
template<class T> const T&
Interval<T>::get_max() const {
  throw_string_if_is_empty();
  return m_max;
}

/*! @brief <B>Exception safety: Strong guarantee.</B>
 ******************************************************************************/
template<class T> bool
Interval<T>::get_is_fp() const {
  return m_is_fp;
}

/*! @brief <B>Exception safety: Strong guarantee.</B>
 ******************************************************************************/
template<class T> T
Interval<T>::get_fp_comparison_tol() const {
  if(not m_is_fp) {
    std::ostringstream oss;
    oss << "requested floating point comparison tolerance for non-floating ";
    oss << "point type";
    throw std::invalid_argument(oss.str());
  }
  return m_fp_comparison_tol;
}

/*! @brief <B>Exception safety: If min <= get_max(), No-throw guarantee.
 *                              Otherwise, Strong guarantee.</B>
 ******************************************************************************/
template<class T> void
Interval<T>::set_min(const T min) {
  m_min = min;
  throw_invalid_argument_if_max_gt_min();
}

/*! @brief <B>Exception safety: If max >= get_min(), No-throw guarantee.
 *                              Otherwise, Strong guarantee.</B>
 ******************************************************************************/
template<class T> void
Interval<T>::set_max(const T max) {
  m_max = max;
  throw_invalid_argument_if_max_gt_min();
}

/*! @brief <B>Exception safety: No-throw guarantee.</B>
 ******************************************************************************/
template<class T> bool
Interval<T>::is_superset_of(T val) const {
  bool ret;
  if(this->get_is_empty()) {
    ret = false;
  }
  else {
    ret = (m_min <= val) and (m_max >= val);
  }
  return ret;
}

/*! @brief <B>Exception safety: No-throw guarantee.</B>
 ******************************************************************************/
template<class T> bool
Interval<T>::is_superset_of(const Interval& interval) const {
  bool ret;
  if(this->get_is_empty()) {
    ret = interval.get_is_empty();
  }
  else {
    if(interval.get_is_empty()) {
      ret = false;
    }
    else {
      ret = (m_min <= interval.get_min()) and (m_max >= interval.get_max());
    }
  }
  return ret;
}

/*! @brief <B>Exception safety: No-throw guarantee.</B>
 ******************************************************************************/
template<class T> bool
Interval<T>::is_proper_superset_of(T val) const {
  bool ret;
  if(this->get_is_empty()) {
    ret = false;
  }
  else {
    ret = (m_min < val) and (m_max > val);
  }
  return ret;
}

/*! @brief <B>Exception safety: No-throw guarantee.</B>
 ******************************************************************************/
template<class T> bool
Interval<T>::is_proper_superset_of(const Interval& interval) const {
  bool ret;
  if(this->get_is_empty()) {
    ret = interval.get_is_empty();
  }
  else {
    if(interval.get_is_empty()) {
      ret = false;
    }
    else {
      ret = (m_min < interval.get_min()) and (m_max > interval.get_max());
    }
  }
  return ret;
}

template<class T> void
Interval<T>::throw_invalid_argument_if_max_gt_min() const {
  if(m_min > m_max) {
    std::ostringstream oss;
    oss << "min (" << m_min << ") ";
    oss << "was > max (" << m_max << ")";
    throw std::invalid_argument(oss.str());
  }
}

template<typename T> std::ostream&
operator<<(std::ostream& os, const Interval<T>& rhs) {
  if(rhs.get_is_empty() or (rhs.get_min() == rhs.get_max())) {
    os << "{"; // start of empty set or single value
  }
  else {
    os << "["; // start of non-empty interval
  }
  if(not rhs.get_is_empty()) {
    os << rhs.get_min();
    if(rhs.get_min() != rhs.get_max()) {
      // see https://en.wikipedia.org/wiki/Interval_(mathematics)#Integer_intervals
      os << "..";
      os << rhs.get_max();
    }
  }
  if(rhs.get_is_empty() or (rhs.get_min() == rhs.get_max())) {
    os << "}"; // end of empty_set or single value
  }
  else {
    os << "]"; // end of non-empty interval
  }
  return os;
}

/*template<typename T>
std::ostream& operator<<(std::ostream& os,
    const Set<T>& rhs) {

  for(auto it=rhs.m_intervals.begin(); it != rhs.m_intervals.end(); ++it) {
    os << *it;
  }
  return os;
}*/

template<> std::ostream&
operator<<(std::ostream& os, const Interval<float>& rhs) {
  float tol = rhs.get_fp_comparison_tol();
  bool min_equals_max = (std::abs(rhs.get_max() - rhs.get_min()) <= tol);
  if(rhs.get_is_empty() or min_equals_max) {
    os << "{"; // start of empty set or single value
  }
  else {
    os << "["; // start of non-empty interval
  }
  if(not rhs.get_is_empty()) {
    os << rhs.get_min();
    float tol = rhs.get_fp_comparison_tol();
    if(std::abs(rhs.get_max() - rhs.get_min()) >= tol) {
      os << ",";
      os << rhs.get_max();
    }
  }
  if(rhs.get_is_empty() or min_equals_max) {
    os << "}"; // end of empty_set or single value
  }
  else {
    os << "]"; // end of non-empty interval
  }
  return os;
}

template<> std::ostream&
operator<<(std::ostream& os, const Interval<double>& rhs) {
  double tol = rhs.get_fp_comparison_tol();
  bool min_equals_max = (std::abs(rhs.get_max() - rhs.get_min()) <= tol);
  if(rhs.get_is_empty() or min_equals_max) {
    os << "{"; // start of empty set or end of single value
  }
  else {
    os << "["; // start of non-empty interval
  }
  if(not rhs.get_is_empty()) {
    os << rhs.get_min();
    if(not min_equals_max) {
      os << ",";
      os << rhs.get_max();
    }
  }
  if(rhs.get_is_empty() or min_equals_max) {
    os << "}"; // end of empty_set or end of single value
  }
  else {
    os << "]"; // end of non-empty interval
  }
  return os;
}

/*! @brief <B>Exception safety: No-throw guarantee.</B>
 ******************************************************************************/
template<class T>
Set<T>::Set() : SetBase() {
}

template<class T>
Set<T>::Set(const Interval<T>& interval) : SetBase() {
  if(not interval.get_is_empty()) {
    m_is_empty = false;
  }
  m_intervals.push_back(interval);
}

template<class T>
Set<T>::Set(const std::vector<Interval<T> >& intervals) : SetBase() {
  for(auto it=intervals.begin(); it!=intervals.end(); ++it) {
    if(not it->get_is_empty()) {
      m_is_empty = false;
      break;
    }
  }
  m_intervals = intervals;
}

template<class T> const std::vector<Interval<T> >&
Set<T>::get_intervals() const {
  return m_intervals;
}

template<class T> T
Set<T>::get_min() const {
  T ret;
  if(m_intervals.size() > 0) {
    ret = m_intervals[0].get_min();
  }
  else {
    throw std::string("requested min for empty set");
  }
  return ret;
}

template<class T>
T Set<T>::get_max() const {
  T ret;
  if(m_intervals.size() > 0) {
    ret = m_intervals[0].get_max();
  }
  else {
    throw std::string("requested max for empty set");
  }
  return ret;
}

template<class T> bool
Set<T>::operator==(const Set<T>& rhs) const {
  return m_intervals == rhs.get_intervals();
}

template<class T> bool
Set<T>::operator!=(const Set<T>& rhs) const {
  return not(*this == rhs);
}

template<typename T> std::ostream&
operator<<(std::ostream& os, const Set<T>& rhs) {
  if(rhs.get_is_empty() or (rhs.get_intervals().size() != 1)) {
    os << "{"; // set start
  }
  if(not rhs.get_is_empty()) {
    auto it = rhs.get_intervals().begin(); 
    for(; it != rhs.get_intervals().end(); ++it) {
      os << *it;
      if(it+1 != rhs.get_intervals().end()) {
        os << ","; // interval separator
      }
    }
  }
  if(rhs.get_is_empty() or (rhs.get_intervals().size() != 1)) {
    os << "}"; // set end
  }
  return os;
}

/// @brief https://en.wikipedia.org/wiki/Union_(set_theory)
template<typename T> Set<T>
union_of(const Interval<T>& first, const Interval<T>& second) {
  return union_of(Set<T>(first), second);
}

/// @brief https://en.wikipedia.org/wiki/Union_(set_theory)
template<typename T> Set<T>
union_of(const Set<T>& set, const Interval<T>& interval) {
  bool do_append = true;
  std::vector<Interval<T> > set_intervals = set.get_intervals();
  for(auto it = set_intervals.begin(); it != set_intervals.end(); ++it) {
    if(interval.get_min() > it->get_max()) {
      // interval                                     *****
      // *it                     ********************
      continue;
    }
    else { // (interval.get_min() <= it->get_max())
      if(interval.get_max() < it->get_min()) {
        // interval       ******
        // *it                     ********************
        set_intervals.insert(it, interval);
        do_append = false;
        break;
      }
      else { // (interval.get_max() >= it->get_min())
        if(interval.get_max() <= it->get_max()) {
          if(interval.get_min() < it->get_min()) {
            // interval             ****************
            // *it                            ********************
            // new *it              ******************************
            it->set_min(interval.get_min());
            do_append = false;
            break;
          }
          else { // interval.get_min() >= it->get_max()
            // interval                         ****
            // *it                            ********************
            // new *it                        ********************
            do_append = false;
            break;
          }
        }
        else { // (interval.get_max() > it->get_max())
          if(interval.get_min() <= it->get_min()) {
            // interval                  ****************************
            // *it                            ********************
            it->set_min(interval.get_min());
          }
          // interval                                         *****
          // *it                            ********************
          it->set_max(interval.get_max());
          auto to_end = it+1;
          // because we expanded *it, we need to handle cases
          // where *it was expanded to overlap *(it+1)
          while(to_end != set_intervals.end()) {
            if(it->get_max() < to_end->get_min()) {
              break; // all overlapping entries have been handled
            }
            else { // (it->get_max() >= to_end->get_min())
              it->set_max(to_end->get_max());
              set_intervals.erase(to_end);
            }
          }
          do_append = false;
          break;
        }
      }
    }
  }
  if(do_append) {
    // if this point is reached, it means interval is higher than any
    // other existing set_intervals so it must be appended
    set_intervals.push_back(interval);
  }
  return Set<T>(set_intervals);
}

/// @brief https://en.wikipedia.org/wiki/Intersection_(set_theory)
template<typename T> Set<T>
intersection_of(const Interval<T>& first, const Interval<T>& second) {
  std::vector<Interval<T> > set_intervals;
  if(second.get_max() >= first.get_min()) {
    T min = first.get_min();
    if(second.get_min() > min) {
      min = second.get_min();
    }
    T max = first.get_max();
    if(second.get_max() < max) {
      max = second.get_max();
    }
    Interval<T> interval(min, max);;
    set_intervals.push_back(interval);
  }
  auto ret = Set<T>(set_intervals);
  if(first.get_is_empty()) {
    ret.set_is_empty(true);
  }
  if(second.get_is_empty()) {
    ret.set_is_empty(true);
  }
  return ret;
}

/// @brief https://en.wikipedia.org/wiki/Intersection_(set_theory)
template<typename T> Set<T>
intersection_of(const Set<T>& set, const Interval<T>& interval) {
  std::vector<Interval<T> > set_intervals = set.get_intervals();
  auto it = set_intervals.begin();
  while(it != set_intervals.end()) {
    T iv_min = interval.get_min();
    T iv_max = interval.get_max();
    if((iv_max < it->get_min()) or (iv_min > it->get_max())) {
      it = set_intervals.erase(it);
    }
    else {
      bool override_min = false;
      bool override_max = false;
      if((iv_min > it->get_min()) && (iv_min <= it->get_max())) {
        override_min = true;
      }
      if((iv_max >= it->get_min()) && (iv_max <= it->get_max())) {
        override_max = true;
      }
      if(override_min) {
        it->set_min(iv_min);
      }
      if(override_max) {
        it->set_max(iv_max);
      }
      it++;
    }
  }
  return Set<T>(set_intervals);
}

CSPSolver::Constr::Constr(const char* lhs, const char* type, const int32_t rhs,
    //CSPSolver::Constr::Cond* p_cond) : Func(lhs, type, ""),
    int32_t idx_cond) : Func(lhs, type, ""),
    m_rhs_int32_const(rhs),
    m_rhs_double_const(0),
    m_rhs_func(0),
    m_rhs_is_var(false),
    m_rhs_is_int32_const(true),
    m_rhs_is_double_const(false),
    m_rhs_is_func(false),
    //m_p_cond(p_cond),
    m_idx_cond(idx_cond),
    m_cond_is_otherwise(false) {
  throw_invalid_argument_if_constraint_not_supported();
}

CSPSolver::Constr::Constr(const char* lhs, const char* type, const double rhs,
    //CSPSolver::Constr::Cond* p_cond) : Func(lhs, type, ""),
    int32_t idx_cond) : Func(lhs, type, ""),
    m_rhs_int32_const(0),
    m_rhs_double_const(rhs),
    m_rhs_func(0),
    m_rhs_is_var(false),
    m_rhs_is_int32_const(false),
    m_rhs_is_double_const(true),
    m_rhs_is_func(false),
    //m_p_cond(p_cond),
    m_idx_cond(idx_cond),
    m_cond_is_otherwise(false) {
  throw_invalid_argument_if_constraint_not_supported();
}

CSPSolver::Constr::Constr(const char* lhs, const char* type, const char* rhs,
    //CSPSolver::Constr::Cond* p_cond) : Func(lhs, type, rhs),
    int32_t idx_cond) : Func(lhs, type, rhs),
    m_rhs_int32_const(0),
    m_rhs_double_const(0),
    m_rhs_func(0),
    m_rhs_is_var(true),
    m_rhs_is_int32_const(false),
    m_rhs_is_double_const(false),
    m_rhs_is_func(false),
    //m_p_cond(p_cond),
    m_idx_cond(idx_cond),
    m_cond_is_otherwise(false) {
  throw_invalid_argument_if_constraint_not_supported();
}

CSPSolver::Constr::Constr(bool cond_is_otherwise) :
    Func("", "", ""),
    m_rhs_int32_const(0),
    m_rhs_double_const(0),
    m_rhs_func(0),
    m_rhs_is_var(false),
    m_rhs_is_int32_const(false),
    m_rhs_is_double_const(false),
    m_rhs_is_func(false),
    //m_p_cond(0),
    m_idx_cond(0),
    m_cond_is_otherwise(cond_is_otherwise) {
}

CSPSolver::OtherwiseCond::OtherwiseCond() : CSPSolver::Constr::Constr(true) {
}

void CSPSolver::Constr::
    throw_invalid_argument_if_constraint_not_supported() {
  bool constraint_is_supported = false;
  constraint_is_supported |= (std::string(m_type) == ">=");
  constraint_is_supported |= (std::string(m_type) == ">");
  constraint_is_supported |= (std::string(m_type) == "<=");
  constraint_is_supported |= (std::string(m_type) == "<");
  constraint_is_supported |= (std::string(m_type) == "=");
  if(not constraint_is_supported) {
    std::ostringstream oss;
    oss << "invalid constraint specified: " << m_type;
    throw std::invalid_argument(oss.str());
  }
}

bool CSPSolver::Constr::operator==(const CSPSolver::Constr& rhs) const {
  bool ret = true;
  ret = (std::string(m_lhs)    != std::string(rhs.m_lhs)) ? false : ret;
  ret = (std::string(m_type)   != std::string(rhs.m_type)) ? false : ret;
  ret = (std::string(m_rhs)    != std::string(rhs.m_rhs)) ? false : ret;
  ret = (m_rhs_int32_const     != rhs.m_rhs_int32_const) ? false : ret;
  ret = (m_rhs_double_const    != rhs.m_rhs_double_const) ? false : ret;
  ret = (m_rhs_func            != rhs.m_rhs_func) ? false : ret;
  ret = (m_rhs_is_var          != rhs.m_rhs_is_var) ? false : ret;
  ret = (m_rhs_is_int32_const  != rhs.m_rhs_is_int32_const) ? false : ret;
  ret = (m_rhs_is_double_const != rhs.m_rhs_is_double_const) ? false : ret;
  ret = (m_rhs_is_func         != rhs.m_rhs_is_func) ? false : ret;
  //ret = (m_p_cond              != rhs.m_p_cond) ? false : ret;
  ret = (m_idx_cond            != rhs.m_idx_cond) ? false : ret;
  return ret;
}

bool
CSPSolver::FeasibleRegionLimits::Var::contains(Interval<int32_t> interval) {
  bool ret = false;
  if(m_type_is_int32) {
    ret = intersection_of(m_int32_set, interval).get_intervals().size() > 0;
  }
  else if(m_type_is_double) {
    Interval<double> iv_double(interval);
    ret = intersection_of(m_double_set, iv_double).get_intervals().size() > 0;
  }
  return ret;
}

bool
CSPSolver::FeasibleRegionLimits::Var::contains(Interval<double> interval) {
  bool ret = false;
  if(m_type_is_int32) {
    throw std::string("not a valid thing to do");
  }
  else if(m_type_is_double) {
    ret = intersection_of(m_double_set, interval).get_intervals().size() > 0;
  }
  //std::cout << m_double_set << "\n";
  return ret;
}

bool
CSPSolver::FeasibleRegionLimits::Var::get_is_empty() {
  bool ret;
  if(m_type_is_int32) {
    ret = m_int32_set.get_is_empty();
  }
  else {
    ret = m_double_set.get_is_empty();
  }
  return ret;
}

Interval<int32_t>
CSPSolver::FeasibleRegionLimits::get_int32_interval_limits() {
  int32_t max = std::numeric_limits<int32_t>::max();
  int32_t min = std::numeric_limits<int32_t>::min();
  return Interval<int32_t>(min, max);
}

Interval<double>
CSPSolver::FeasibleRegionLimits::get_double_interval_limits(double tol) {
  double max = std::numeric_limits<double>::max();
  double min = -max;
  return Interval<double>(min, max, tol);
}

void
CSPSolver::FeasibleRegionLimits::set_var_limits_to_type_limits(
    std::pair<const char* const, FeasibleRegionLimits::Var>& var) {
  if(var.second.m_type_is_int32) {
    var.second.m_int32_set = Set<int32_t>(get_int32_interval_limits());
  }
  else if(var.second.m_type_is_double) {
    double tol = var.second.m_fp_comparison_tol;
    var.second.m_double_set = Set<double>(get_double_interval_limits(tol));
  }
}

void
CSPSolver::FeasibleRegionLimits::set_var_limits_to_empty_set(
    std::pair<const char* const, FeasibleRegionLimits::Var>& var) {
  if(var.second.m_type_is_int32) {
    var.second.m_int32_set.set_is_empty(true);
  }
  else if(var.second.m_type_is_double) {
    var.second.m_double_set.set_is_empty(true);
  }
}

bool
CSPSolver::FeasibleRegionLimits::operator==(
    const CSPSolver::FeasibleRegionLimits& rhs) const {
  bool ret = true;
  for(auto it = m_vars.begin(); it != m_vars.end(); ++it) {
    //if(it->second.m_type_is_double) {
      auto itrhs = rhs.m_vars.begin();
      for(; itrhs != rhs.m_vars.end(); ++itrhs) {
        if(it->first == itrhs->first) { // if var key matches
          if(it->second.m_type_is_int32 != itrhs->second.m_type_is_int32) {
            ret = false;
            break;
          }
          if(it->second.m_type_is_double != itrhs->second.m_type_is_double) {
            ret = false;
            break;
          }
          if(it->second.m_type_is_int32) {
            if(it->second.m_int32_set != itrhs->second.m_int32_set ) {
              ret = false;
              break;
            }
          }
          else if(it->second.m_type_is_double) {
            if(it->second.m_double_set != itrhs->second.m_double_set) {
              ret = false;
              break;
            }
          }
        }
      }
    //}
    if(ret == false) {
      break;
    }
  }
  return ret;
}

bool
CSPSolver::FeasibleRegionLimits::operator!=(
    const CSPSolver::FeasibleRegionLimits& rhs) const {
  return not(*this == rhs);
}

std::ostream&
operator<<(std::ostream& os, const CSPSolver::FeasibleRegionLimits::Var& var) {
  if(var.m_type_is_int32) {
    os << var.m_int32_set;
  }
  else if(var.m_type_is_double) {
    os << var.m_double_set;
  }
  return os;
}

std::ostream&
operator<<(std::ostream& os, const CSPSolver::FeasibleRegionLimits& rhs) {
  bool first = true;
  os << "<";
  for(auto it = rhs.m_vars.begin(); it != rhs.m_vars.end(); ++it) {
    if(not first) {
      os << ",";
    }
    first = false;
    os << it->first << ":" << it->second;
  }
  os << ">";
  return os;
}

CSPSolver::CSPSolver(size_t max_num_constr_prop_loop_iter) :
  m_max_num_constr_prop_loop_iter(max_num_constr_prop_loop_iter) {
}

template<> void
CSPSolver::add_var<int32_t> (const char* var_key) {
  // step 1: initial dilation
  int32_t hi = std::numeric_limits<int32_t>::max();
  int32_t lo = std::numeric_limits<int32_t>::min();
  typedef FeasibleRegionLimits::Var Var;
  m_feasible_region_limits.m_vars.insert(std::make_pair(var_key, Var(lo, hi)));
}

template<> void
CSPSolver::add_var<double> (const char* var_key,
    double fp_comparison_tol) {
  // step 1: initial dilation
  double hi = std::numeric_limits<double>::max();
  double lo = -hi;
  typedef FeasibleRegionLimits::Var Var;
  double tol = fp_comparison_tol;
  const char*& key = var_key;
  m_feasible_region_limits.m_vars.insert(std::make_pair(key, Var(lo, hi, tol)));
}

template<typename T> CSPSolver::Constr&
CSPSolver::add_constr(const char* lhs, const char* type, const T rhs) {
  throw_invalid_argument_if_var_key_has_not_been_added(lhs);
  m_constr.push_back(Constr(lhs, type, rhs, 0));
  propagate_constraints();
  return m_constr.at(m_constr.size()-1);
}

template<typename T> CSPSolver::Constr&
CSPSolver::add_constr(const char* lhs, const char* type, const T rhs, const Constr::Cond& cond) {
  throw_invalid_argument_if_var_key_has_not_been_added(lhs);
  bool cond_exists = false;
  for(auto it=m_cond.begin(); it!=m_cond.end(); ++it) {
    if(*it == cond) {
      cond_exists = true;
      break;
    }
  }
  if(!cond_exists) { // only append unique conditions (this is an optimization)
    m_cond.push_back(cond);
  }
  //m_constr.push_back(Constr(lhs, type, rhs, &m_cond.back()));
  m_constr.push_back(Constr(lhs, type, rhs, m_cond.size()));
  propagate_constraints();
  return m_constr.at(m_constr.size()-1);
}

void
CSPSolver::remove_constr(const Constr& constr) {
  for(auto it=m_constr.begin(); it!=m_constr.end(); ++it) {
    if(*it == constr) {
      m_constr.erase(it);
      break;
    }
  }
  propagate_constraints();
}

const std::vector<CSPSolver::Constr>&
CSPSolver::get_constr() const {
  return m_constr;
}

const CSPSolver::FeasibleRegionLimits&
CSPSolver::get_feasible_region_limits() const {
  return m_feasible_region_limits;
}

bool
CSPSolver::feasible_region_limits_is_empty_for_var(const char* var) const {
  bool ret;
  auto lims = m_feasible_region_limits.m_vars.at(var);
  if(lims.m_type_is_int32) {
    ret = lims.m_int32_set.get_is_empty();
  }
  else {
    ret = lims.m_double_set.get_is_empty();
  }
  return ret;
}

const CSPSolver::FeasibleRegionLimits::Var&
CSPSolver::get_feasible_region_limits(const char* var) const {
  return m_feasible_region_limits.m_vars.at(var);
}

/// @return minimum as a double, regardless of whether var is an int32 or not
double
CSPSolver::get_feasible_region_limits_min_double(const char* var) const {
  double ret;
  auto lims = m_feasible_region_limits.m_vars.at(var);
  if(lims.m_type_is_int32) {
    ret = (double) lims.m_int32_set.get_min();
  }
  else {
    ret = lims.m_double_set.get_min();
  }
  return ret;
}

bool
CSPSolver::get_var_has_been_added(const char* var_key) const {
  const FeasibleRegionLimits& limits = m_feasible_region_limits;
  return limits.m_vars.find(var_key) != limits.m_vars.end();
}

template<typename T> bool
CSPSolver::val_is_within_var_feasible_region(T val, const char* var_key) const {
  const FeasibleRegionLimits& limits = m_feasible_region_limits;
  return limits.m_vars.find(var_key) != limits.m_vars.end();
}

Interval<int32_t>
CSPSolver::get_interval_for_constr(Constr constr) {
  int32_t min, max;
  if(std::string(constr.m_type) == ">=") {
    min = constr.m_rhs_int32_const;
    max = std::numeric_limits<int32_t>::max();
  }
  else if(std::string(constr.m_type) == ">") {
    min = constr.m_rhs_int32_const+1;
    max = std::numeric_limits<int32_t>::max();
  }
  else if(std::string(constr.m_type) == "<=") {
    min = std::numeric_limits<int32_t>::min();
    max = constr.m_rhs_int32_const;
  }
  else if(std::string(constr.m_type) == "<") {
    min = std::numeric_limits<int32_t>::min();
    max = constr.m_rhs_int32_const-1;
  }
  else if(std::string(constr.m_type) == "=") {
    min = constr.m_rhs_int32_const;
    max = constr.m_rhs_int32_const;
  }
  return Interval<int32_t>(min, max);
}

Interval<double>
CSPSolver::get_interval_for_constr(Constr constr, double tol) {
  double min, max;
  if(std::string(constr.m_type) == ">=") {
    min = constr.m_rhs_double_const;
    max = std::numeric_limits<double>::max();
  }
  else if(std::string(constr.m_type) == ">") {
    ///@TODO/FIXME - add unit test for replacement of below line
    //min = constr.m_rhs_double_const+(-DBL_MAX);
    min = constr.m_rhs_double_const+FLT_MIN;
    max = std::numeric_limits<double>::max();
  }
  else if(std::string(constr.m_type) == "<=") {
    min = -std::numeric_limits<double>::max();
    max = constr.m_rhs_double_const;
  }
  else if(std::string(constr.m_type) == "<") {
    min = -std::numeric_limits<double>::max();
    ///@TODO/FIXME - add unit test for replacement of below line
    //max = constr.m_rhs_double_const-(-DBL_MAX);
    max = constr.m_rhs_double_const-FLT_MIN;
  }
  else if(std::string(constr.m_type) == "=") {
    min = constr.m_rhs_double_const;
    max = constr.m_rhs_double_const;
  }
  return Interval<double>(min, max, tol);
}

void
CSPSolver::dilate(
    std::pair<const char* const, FeasibleRegionLimits::Var>& var,
    Interval<int32_t>& iv) {
  if(var.second.m_int32_set.get_is_empty()) {
    var.second.m_int32_set = Set<int32_t>(iv);
  }
  else {
    var.second.m_int32_set = union_of(var.second.m_int32_set, iv);
  }
}

void
CSPSolver::dilate(
    std::pair<const char* const, FeasibleRegionLimits::Var>& var,
    Interval<double>& iv) {
  if(var.second.m_double_set.get_is_empty()) {
    var.second.m_double_set = Set<double>(iv);
  }
  else {
    var.second.m_double_set = union_of(var.second.m_double_set, iv);
  }
}

void
CSPSolver::erode(
    std::pair<const char* const, FeasibleRegionLimits::Var>& var,
    Interval<int32_t>& iv) {
  var.second.m_int32_set = intersection_of(var.second.m_int32_set, iv);
}

void
CSPSolver::erode(
    std::pair<const char* const, FeasibleRegionLimits::Var>& var,
    Interval<double>& iv) {
  var.second.m_double_set = intersection_of(var.second.m_double_set, iv);
}

void
CSPSolver::propagate_constr_rhs_const(
    std::pair<const char* const, FeasibleRegionLimits::Var>& ivar,
    Constr& constr, /*const std::vector<CSPSolver::CondConstr>& cc*/ bool do_dilate) {
  // if lhs var is empty set, then there is nothing to do for forward
  // constraint (can't further constrain an empty set) or reverse constraint
  // (can't constraint the rhs constant)
  //if(not ivar.second.get_is_empty()) {
    //bool var_is_cond_constr = cc.size() > 0;
    //bool dilation = false;
    Set<int32_t> cc_set_int32;
    Set<double> cc_set_double;
    if(ivar.second.m_type_is_int32) {
      assign_set_to_domain_limits(cc_set_int32, 0);
    }
    else if(ivar.second.m_type_is_double) {
      assign_set_to_domain_limits(cc_set_double, ivar.second.m_fp_comparison_tol);
    }
    bool cond_possible = false;
    //std::cout << "ccsize " << cc.size() << "\n";
    //for(auto it=cc.begin(); it!=cc.end(); ++it) {
    if(constr.m_idx_cond/*constr.m_p_cond*/) { // is conditional
      //FeasibleRegionLimits::Var* cvar = 0;
      //cvar = &m_feasible_region_limits.m_vars.at(it->m_cv);
      //auto& tmp = m_feasible_region_limits.m_vars.at(constr.m_p_cond->m_lhs);
      if(m_cond[constr.m_idx_cond-1].m_cond_is_otherwise) {
        cond_possible = true; /// @TODO/FIXME change this line
      }
      else {
        auto& tmp = m_feasible_region_limits.m_vars.at(m_cond[constr.m_idx_cond-1].m_lhs);
        if(m_cond[constr.m_idx_cond-1].m_rhs_is_int32_const/*constr.m_p_cond->m_rhs_is_int32_const*/) {
          Interval<int32_t> tmp_iv = get_interval_for_constr((Constr)m_cond[constr.m_idx_cond-1]/*constr.m_p_cond*/);
          //cond_possible = cvar->contains(tmp_iv);
          cond_possible = tmp.contains(tmp_iv);
        }
        else if(m_cond[constr.m_idx_cond-1].m_rhs_is_double_const/*constr.m_p_cond->m_rhs_is_double_const*/) {
          double tol = tmp.m_fp_comparison_tol;
          Interval<double> tmp_iv = get_interval_for_constr((Constr)m_cond[constr.m_idx_cond-1]/*constr.m_p_cond*/, tol);
          //cond_possible = cvar->contains(tmp_iv);
          cond_possible = tmp.contains(tmp_iv);
        }
        else if(m_cond[constr.m_idx_cond-1].m_rhs_is_var/*constr.m_p_cond->m_rhs_is_var*/) {
          throw std::string("this scenario not yet supported");
        }
      }
      Interval<int32_t> tmp_iv = get_interval_for_constr((Constr)m_cond[constr.m_idx_cond-1]/*constr.m_p_cond*/);
      if(cond_possible) {
        if(ivar.second.m_type_is_int32) {
          Interval<int32_t> iv = get_interval_for_constr(constr);
          //std::cout << "iv " << iv << "\n";
          cc_set_int32 = intersection_of(cc_set_int32, iv);
        }
        else if(ivar.second.m_type_is_double) {
          double tol = ivar.second.m_fp_comparison_tol;
          Interval<double> iv = get_interval_for_constr(constr, tol);
          //std::cout << "iv " << iv << "\n";
          cc_set_double = intersection_of(cc_set_double, iv);
        }
      }
    }
    //}
    if(ivar.second.m_type_is_int32) {
      // forward interval
      Interval<int32_t> ivf = get_interval_for_constr(constr);
      /*if(var_is_cond_constr and cond_possible) {
        //std::cout << "dilate " << ivar.first << " by interval " << ivf << "\n";
      }
      else {
        //std::cout << "erode " << ivar.first << " by interval " << ivf << "\n";
      }*/

      // forward constraint
      //(var_is_cond_constr and cond_possible) ? dilate(ivar, ivf) : erode(ivar, ivf);
      if(do_dilate) {
        if(cond_possible) {
          dilate(ivar, ivf);
        }
      }
      else {
        erode(ivar, ivf);
      }
    }
    else if(ivar.second.m_type_is_double) {
      // forward interval
      double tol = ivar.second.m_fp_comparison_tol;
      Interval<double> ivf = get_interval_for_constr(constr, tol);
      /*if(var_is_cond_constr and cond_possible) {
        //std::cout << "dilate " << ivar.first << " by interval " << ivf << "\n";
      }
      else {
        //std::cout << "erode " << ivar.first << " by interval " << ivf << "\n";
      }*/
      // forward constraint
      //(var_is_cond_constr and cond_possible) ? dilate(ivar, ivf) : erode(ivar, ivf);
      if(do_dilate) {
        if(cond_possible) {
          dilate(ivar, ivf);
        }
      }
      else {
        erode(ivar, ivf);
      }
    }
  //}
}

void
CSPSolver::propagate_constr_rhs_var(
    std::pair<const char* const, FeasibleRegionLimits::Var>& ivar,
    Constr& constr, /*const std::vector<CSPSolver::CondConstr>& cc*/ bool do_dilate) {
  assert(!do_dilate); /// @TODO / FIXME remove
  /*bool var_is_cond_constr = cc.size() > 0;
  if(var_is_cond_constr) {
    throw std::string("this scenario not yet supported");
  }*/
  auto& vars = m_feasible_region_limits.m_vars;
  auto& rhs = vars.at(constr.m_rhs);
  //bool dilation = false;
  bool cond_possible = false;
  // forward constraint (constrain the lhs var by the rhs var)
  if(rhs.m_type_is_double) {
    double min, max;
    auto& set = rhs.m_double_set; // rhs set
    if(set.get_is_empty()) {
      ivar.second.m_double_set.set_is_empty(true);
    }
    else {
      if(std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<double>::max();
      }
      else if(std::string(constr.m_type) == ">") {
        min = set.get_min()+(-DBL_MAX);
        max = std::numeric_limits<double>::max();
      }
      else if(std::string(constr.m_type) == "<=") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max();
      }
      else if(std::string(constr.m_type) == "<") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max()-(-DBL_MAX);
      }
      else if(std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      auto& lhs_set = ivar.second.m_double_set;
      // forward interval
      Interval<double> iv(min, max, ivar.second.m_fp_comparison_tol);
      /*if(constr.m_p_cond) { // dilation
        assert(false);
        bool cond_is_possible = true; /// @TODO set to appropriate value
        if(cond_is_possible) {
          lhs_set = union_of(lhs_set, iv);
        }
      }
      else { // erosion
        lhs_set = intersection_of(lhs_set, iv);
      }*/
      //std::cout << "forward constraint: intersecting " << ivar.first << " with " << iv << "\n";
      lhs_set = intersection_of(lhs_set, iv);
    }
  }
  else {
    int32_t min, max;
    auto& set = rhs.m_int32_set; // rhs set
    if(set.get_is_empty()) {
      ivar.second.m_int32_set.set_is_empty(true);
    }
    else {
      if(std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<int32_t>::max();
      }
      else if(std::string(constr.m_type) == ">") {
        min = set.get_min()+1;
        max = std::numeric_limits<int32_t>::max();
      }
      else if(std::string(constr.m_type) == "<=") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max();
      }
      else if(std::string(constr.m_type) == "<") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max()-1;
      }
      else if(std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      auto& lhs_set = ivar.second.m_int32_set;
      Interval<int32_t> iv(min, max); // forward interval
      /*if(constr.m_p_cond) { // dilation
        assert(false);
        bool cond_is_possible = true; /// @TODO set to appropriate value
        if(cond_is_possible) {
          lhs_set = union_of(lhs_set, iv);
        }
      }
      else { // erosion
        lhs_set = intersection_of(lhs_set, iv);
      }*/
      lhs_set = intersection_of(lhs_set, iv);
    }
  }
  // reverse constraint (constrain the rhs var by the lhs var)
  if(ivar.second.m_type_is_double) {
    double min, max;
    auto& set = ivar.second.m_double_set; // lhs set
    if(set.get_is_empty()) {
      rhs.m_double_set.set_is_empty(true);
    }
    else {
      if(std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<double>::max();
      }
      else if(std::string(constr.m_type) == ">") {
        min = set.get_min()+(-DBL_MAX);
        max = std::numeric_limits<double>::max();
      }
      else if(std::string(constr.m_type) == "<=") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max();
      }
      else if(std::string(constr.m_type) == "<") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max()-(-DBL_MAX);
      }
      else if(std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      // reverse interval
      Interval<double> iv(min, max, ivar.second.m_fp_comparison_tol);
      auto& rhs_set = rhs.m_double_set;
      /*if(constr.m_p_cond) { // dilation
        assert(false);
        bool cond_is_possible = true; /// @TODO set to appropriate value
        if(cond_is_possible) {
          rhs_set = union_of(rhs_set, iv);
        }
      }
      else { // erosion
        rhs_set = intersection_of(rhs_set, iv);
      }*/
      //std::cout << "reverse constraint: intersecting " << constr.m_rhs << " with " << iv << "\n";
      rhs_set = intersection_of(rhs_set, iv);
    }
  }
  else {
    int32_t min, max;
    auto& set = ivar.second.m_int32_set; // lhs set
    if(set.get_is_empty()) {
      rhs.m_int32_set.set_is_empty(true);
    }
    else {
      if(std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<int32_t>::max();
      }
      else if(std::string(constr.m_type) == ">") {
        min = set.get_min()+1;
        max = std::numeric_limits<int32_t>::max();
      }
      else if(std::string(constr.m_type) == "<=") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max();
      }
      else if(std::string(constr.m_type) == "<") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max()-1;
      }
      else if(std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      Interval<int32_t> iv(min, max); // reverse interval
      auto& rhs_set = rhs.m_int32_set;
      /*if(constr.m_p_cond) { // dilation
        assert(false);
        bool cond_is_possible = true; /// @TODO set to appropriate value
        if(cond_is_possible) {
          rhs_set = union_of(rhs_set, iv);
        }
      }
      else { // erosion
        rhs_set = intersection_of(rhs_set, iv);
      }*/
      rhs_set = intersection_of(rhs_set, iv);
    }
  }
}

void
CSPSolver::assign_set_to_domain_limits(Set<int32_t>& set, int32_t tol) {
  int32_t max = std::numeric_limits<int32_t>::max();
  int32_t min = std::numeric_limits<int32_t>::min();
  Interval<int32_t> interval(min, max);
  set = Set<int32_t>(interval);
}

void
CSPSolver::assign_set_to_domain_limits(Set<double>& set, double tol) {
  double max = std::numeric_limits<double>::max();
  double min = -max;
  Interval<double> interval(min, max, tol);
  set = Set<double>(interval);
}

/*void
CSPSolver::set_var_limits_to_empty_set(
    std::pair<const char* const, FeasibleRegionLimits::Var>& ivar) {
  if(ivar.second.m_type_is_int32) {
    ivar.second.m_int32_set = Set<int32_t>();
  }
  else if(ivar.second.m_type_is_double) {
    ivar.second.m_double_set = Set<double>();
  }
}*/

std::vector<CSPSolver::CondConstr>
CSPSolver::find_cond_constrs() {
  std::vector<CSPSolver::CondConstr> ret;
  // iterate over all variables (X)
  auto itvs = m_feasible_region_limits.m_vars.begin(); 
  for(; itvs != m_feasible_region_limits.m_vars.end(); ++itvs) {
    // iterate over all constraints (C)
    for(auto itcs = m_constr.begin(); itcs != m_constr.end(); ++itcs) {
      if(itcs->m_lhs == itvs->first) {
        //std::cout << "found var constrained by " << itcs->m_type << itcs->m_rhs << " " << itcs->m_p_cond << "\n";
        // found constraint for current variable
        if(itcs->m_idx_cond > 0/*itcs->m_p_cond != 0*/) { // found conditional constraint
          //std::cout << "found conditional constraint\n";
          CSPSolver::CondConstr tmp;
          tmp.m_v = itvs->first;
          if(m_cond[itcs->m_idx_cond-1].m_lhs/*itcs->m_p_cond->m_lhs*/) {
            if(strcmp(m_cond[itcs->m_idx_cond-1].m_lhs/*itcs->m_p_cond->m_lhs*/, "") != 0) {
              tmp.m_cv = m_cond[itcs->m_idx_cond-1].m_lhs;//itcs->m_p_cond->m_lhs;
              ret.push_back(tmp);
            }
          }
        }
      }
    }
  }
  return ret;
}

void
CSPSolver::propagate_constraints() {
  // step 1: for all variables, initialize feasibility region to full set
  //         for the respective variable type
  auto _itvs = m_feasible_region_limits.m_vars.begin();
  for(; _itvs != m_feasible_region_limits.m_vars.end(); ++_itvs) {
    m_feasible_region_limits.set_var_limits_to_type_limits(*_itvs);
  }
  std::vector<CSPSolver::CondConstr> vars_constr_cond = find_cond_constrs();
  // propagation_loop:
  bool pending_iter = true;
  ///@TODO / FIXME - ensure developers can override value of max_num...iter
  for(size_t iter=1; iter <= m_max_num_constr_prop_loop_iter; iter++) {
    FeasibleRegionLimits limits_from_prev_iter = m_feasible_region_limits;
    // variable_loop: (iterate over all variables (X))
    auto itvs = m_feasible_region_limits.m_vars.begin(); 
    for(; itvs != m_feasible_region_limits.m_vars.end(); ++itvs) {
      // step 2: assign the current variable's feasibility
      //         region to full set for the respective variable type
      //m_feasible_region_limits.set_var_limits_to_type_limits(*itvs);
      // step 3: if any conditional constraints apply to the current
      //         variable, erode its feasibility region to an empty set
      std::vector<CSPSolver::CondConstr> applied_cond_constrs;
      auto vcc = vars_constr_cond.begin();
      for(; vcc!=vars_constr_cond.end(); ++vcc) {
        if(vcc->m_v == itvs->first) {  // cond constr is applied to current var
          applied_cond_constrs.push_back(*vcc);
        }
      }
      if(applied_cond_constrs.size() > 0) { // any conditional constraints apply
        m_feasible_region_limits.set_var_limits_to_empty_set(*itvs);
      }
      // step 4: if any conditional constraints apply to the current
      //         variable, dilate by the range of each possible condition,
      //         where possible condition is an erosion of the full set
      //         for the respective variable type
      // step 5: if any conditionless constraints apply to the current
      //         variable, erode to the range of each one
      int32_t max_idx_cond = 0;
      for(size_t step=4; step<=6; step++) {
        // iterate over all constraints (C)
        for(auto itcs = m_constr.begin(); itcs != m_constr.end(); itcs++) {
          bool dilate = false; // if false, erode
          bool constraint_is_conditional = itcs->m_idx_cond > 0;//itcs->m_p_cond != 0;
          if(constraint_is_conditional) {
            if(itcs->m_idx_cond > max_idx_cond) { // is first time condition is seen
              dilate = (step == 4);
              max_idx_cond = itcs->m_idx_cond;
            }
          }
          if(itcs->m_lhs == itvs->first) { // constraint is applied to current_var
            bool apply = (step == 4 && constraint_is_conditional);
            apply |= (step == 5 && !constraint_is_conditional);
            apply |= (step == 6);
            if(apply) {
              if(step < 6 && itcs->m_rhs_is_int32_const) {
                propagate_constr_rhs_const(*itvs, *itcs, /*cond_constrs, */dilate);
              }
              else if(step < 6 && itcs->m_rhs_is_double_const) {
                propagate_constr_rhs_const(*itvs, *itcs, /*cond_constrs, */dilate);
              }
              else if(step == 6 && itcs->m_rhs_is_var) {
                propagate_constr_rhs_var(  *itvs, *itcs, /*cond_constrs, */dilate);
              }
            }
          }
        }
      }
    }
    // step 6: goto step 2 until feasibility region stops changing
    if(m_feasible_region_limits == limits_from_prev_iter) {
      pending_iter = false;
      break;
    }
  }
  if(pending_iter) {
    throw std::string("erroneous state - max num propagations loops exceeded");
  }
}

void
CSPSolver::throw_invalid_argument_if_var_key_has_not_been_added(
    const char* var_key) {
  if(not get_var_has_been_added(var_key)) {
    std::ostringstream oss;
    oss << "invalid constraint specified (variable " << var_key;
    oss << " has not been added)";
    throw std::invalid_argument(oss.str());
  }
}

std::ostream&
operator<<(std::ostream& os, const CSPSolver& rhs) {
  os << "<X,D,C>:=<";
  os << "X/D:";
  {
    bool first_var = true;
    auto it = rhs.get_feasible_region_limits().m_vars.begin();
    for(; it != rhs.get_feasible_region_limits().m_vars.end(); ++it) {
      if(not first_var) {
        os << ",";
      }
      first_var = false;
      if(it->second.m_type_is_int32) {
        os << it->first << "/int32";
      }
      if(it->second.m_type_is_double) {
        os << it->first << "/double";
      }
    }
  }
  os << ",C:";
  {
    bool first_var = true;
    auto it = rhs.get_constr().begin();
    for(; it != rhs.get_constr().end(); ++it) {
      if(not first_var) {
        os << ",";
      }
      first_var = false;
      os << it->m_lhs << it->m_type;
      if(it->m_rhs_is_int32_const) {
        os << it->m_rhs_int32_const;
      }
      else if(it->m_rhs_is_double_const) {
        os << it->m_rhs_double_const;
      }
      else if(it->m_rhs_is_var) {
        os << it->m_rhs;
      }
    }
  }
  os << ">";
  return os;
}

} // namespace Math
