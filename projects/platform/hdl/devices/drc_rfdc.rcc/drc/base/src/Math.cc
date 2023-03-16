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
#include <stdexcept>
#include <vector>
#include <map>
#include <limits>
#include <utility> // std::make_pair
#include <cmath> // std::abs(double)
#include <algorithm> // std::min
#include <string> // std::string
#include <cfloat> // DBL_MAX
#include "Math.hh"

std::ostream&
operator<<(std::ostream& os, const CSPSolver::Constr& rhs) {
  os << rhs.m_lhs << rhs.m_type;
  if (rhs.m_rhs_is_int32_const)
    os << rhs.m_rhs_int32_const;
  else if (rhs.m_rhs_is_double_const)
    os << rhs.m_rhs_double_const;
  else if (rhs.m_rhs_is_var)
    os << rhs.m_rhs;
  return os;
}

std::ostream&
operator<<(std::ostream& os, const CSPSolver& rhs) {
  os << "<X,D,C>:=<";
  os << "X/D:";
  bool first_var = true;
  auto it = rhs.get_feasible_region_limits().m_vars.begin();
  for (; it != rhs.get_feasible_region_limits().m_vars.end(); ++it) {
    if (!first_var)
      os << ",";
    first_var = false;
    if (it->second.m_type_is_int32)
      os << it->first << "/int32";
    else
      os << it->first << "/double";
  }
  os << ",C:";
  bool first_var2 = true;
  auto it2 = rhs.get_constr().begin();
  for (; it2 != rhs.get_constr().end(); ++it2) {
    if (!first_var2)
      os << ",";
    first_var2 = false;
    os << it2->second;
  }
  os << ">";
  return os;
}

SetBase::SetBase() : m_is_empty(true) {
}

void
SetBase::throw_if_is_empty() const {
  if (m_is_empty)
    throw std::runtime_error("performed op on min/max of empty interval");
}

const bool&
SetBase::get_is_empty() const {
  return m_is_empty;
}

void
SetBase::set_is_empty(bool val) {
  m_is_empty = val;
}

template<class T>
_Interval<T>::_Interval() : SetBase(), m_is_fp(false) {
}

template<class T>
_Interval<T>::_Interval(T min, T max) :
    SetBase(), m_min(min), m_max(max), m_is_fp(false) {
  m_is_empty = false;
  throw_invalid_argument_if_max_gt_min();
}

template<class T>
_Interval<T>::_Interval(const _Interval<int32_t>& obj) :
    SetBase(), m_min(obj.get_min()), m_max(obj.get_max()), m_is_fp(false) {
  m_is_empty = false;
  throw_invalid_argument_if_max_gt_min();
}

template<>
_Interval<double>::_Interval(double min, double max, double fp_comparison_tol) :
    SetBase(), m_min(min), m_max(max), m_is_fp(true),
    m_fp_comparison_tol(fp_comparison_tol) {
  if (m_fp_comparison_tol <= 0) {
    std::ostringstream oss;
    oss << "_Interval object constructed with invalid tolerance comparison ";
    oss << "value of " << m_fp_comparison_tol;
    throw std::invalid_argument(oss.str());
  }
  m_is_empty = false;
  throw_invalid_argument_if_max_gt_min();
}

template<class T>
_Interval<T>::_Interval(T min, T max, T fp_comparison_tol) :
    SetBase(), m_min(min), m_max(max), m_is_fp(false),
    m_fp_comparison_tol(fp_comparison_tol) {
  std::ostringstream oss;
  oss << "_Interval object constructed for non-floating point type but still ";
  oss << "specified comparison tolerance";
  throw std::invalid_argument(oss.str());
}

template<class T> bool
_Interval<T>::operator==(const _Interval<T>& rhs) const {
  if (m_is_fp != rhs.get_is_fp())
    return false;
  if (m_min != rhs.get_min())
    return false;
  if (m_max != rhs.get_max())
    return false;
  return true;
}

template<> bool
_Interval<double>::operator==(const _Interval<double>& rhs) const {
  if (m_is_fp != rhs.get_is_fp())
    return false;
  // m_is_fp is guaranteed to be true by constructor
  if (std::abs(m_min - rhs.get_min()) > m_fp_comparison_tol)
    return false;
  if (std::abs(m_max - rhs.get_max()) > m_fp_comparison_tol)
    return false;
  return true;
}

template<class T> const T&
_Interval<T>::get_min() const {
  throw_if_is_empty();
  return m_min;
}

template<class T> const T&
_Interval<T>::get_max() const {
  throw_if_is_empty();
  return m_max;
}

template<class T> bool
_Interval<T>::get_is_fp() const {
  return m_is_fp;
}

template<class T> T
_Interval<T>::get_fp_comparison_tol() const {
  if (!m_is_fp) {
    std::ostringstream oss;
    oss << "requested floating point comparison tolerance for non-floating ";
    oss << "point type";
    throw std::invalid_argument(oss.str());
  }
  return m_fp_comparison_tol;
}

template<class T> void
_Interval<T>::set_min(const T min) {
  m_min = min;
  throw_invalid_argument_if_max_gt_min();
}

template<class T> void
_Interval<T>::set_max(const T max) {
  m_max = max;
  throw_invalid_argument_if_max_gt_min();
}

template<class T> bool
_Interval<T>::is_superset_of(T val) const {
  bool ret;
  if (this->get_is_empty())
    ret = false;
  else
    ret = (m_min <= val) && (m_max >= val);
  return ret;
}

template<class T> bool
_Interval<T>::is_superset_of(const _Interval& interval) const {
  bool ret;
  if (this->get_is_empty()) {
    ret = interval.get_is_empty();
  }
  else {
    if (interval.get_is_empty())
      ret = false;
    else
      ret = (m_min <= interval.get_min()) && (m_max >= interval.get_max());
  }
  return ret;
}

template<class T> bool
_Interval<T>::is_proper_superset_of(T val) const {
  bool ret;
  if (this->get_is_empty())
    ret = false;
  else
    ret = (m_min < val) && (m_max > val);
  return ret;
}

template<class T> bool
_Interval<T>::is_proper_superset_of(const _Interval& interval) const {
  bool ret;
  if (this->get_is_empty()) {
    ret = interval.get_is_empty();
  }
  else {
    if (interval.get_is_empty())
      ret = false;
    else
      ret = (m_min < interval.get_min()) && (m_max > interval.get_max());
  }
  return ret;
}

template<class T> void
_Interval<T>::throw_invalid_argument_if_max_gt_min() const {
  if (m_min > m_max) {
    std::ostringstream oss;
    oss << "min (" << m_min << ") ";
    oss << "was > max (" << m_max << ")";
    throw std::invalid_argument(oss.str());
  }
}

template<typename T> std::ostream&
operator<<(std::ostream& os, const _Interval<T>& rhs) {
  if (rhs.get_is_empty() || (rhs.get_min() == rhs.get_max()))
    os << "{"; // start of empty set or single value
  else
    os << "["; // start of non-empty interval
  if (!rhs.get_is_empty()) {
    os << rhs.get_min();
    if (rhs.get_min() != rhs.get_max()) {
      // https://en.wikipedia.org/wiki/_Interval_(mathematics)#Integer_intervals
      os << "..";
      os << rhs.get_max();
    }
  }
  if (rhs.get_is_empty() || (rhs.get_min() == rhs.get_max()))
    os << "}"; // end of empty_set or single value
  else
    os << "]"; // end of non-empty interval
  return os;
}

/*template<typename T>
std::ostream& operator<<(std::ostream& os,
    const Set<T>& rhs) {
  for (auto it=rhs.m_intervals.begin(); it != rhs.m_intervals.end(); ++it) {
    os << *it;
  }
  return os;
}*/

template<> std::ostream&
operator<<(std::ostream& os, const _Interval<double>& rhs) {
  double tol = rhs.get_fp_comparison_tol();
  bool min_equals_max = (std::abs(rhs.get_max() - rhs.get_min()) <= tol);
  if (rhs.get_is_empty() || min_equals_max)
    os << "{"; // start of empty set or end of single value
  else
    os << "["; // start of non-empty interval
  if (!rhs.get_is_empty()) {
    os << rhs.get_min();
    if (!min_equals_max) {
      os << ",";
      os << rhs.get_max();
    }
  }
  if (rhs.get_is_empty() || min_equals_max)
    os << "}"; // end of empty_set or end of single value
  else
    os << "]"; // end of non-empty interval
  return os;
}

template<class T>
Set<T>::Set() : SetBase() {
}

template<class T>
Set<T>::Set(const _Interval<T>& interval) : SetBase() {
  if (!interval.get_is_empty())
    m_is_empty = false;
  m_intervals.push_back(interval);
}

template<class T>
Set<T>::Set(const std::vector<_Interval<T> >& intervals) : SetBase() {
  for (auto it=intervals.begin(); it!=intervals.end(); ++it)
    if (!it->get_is_empty()) {
      m_is_empty = false;
      break;
    }
  m_intervals = intervals;
}

template<class T> const std::vector<_Interval<T> >&
Set<T>::get_intervals() const {
  return m_intervals;
}

template<class T> T
Set<T>::get_min() const {
  T ret;
  if (m_intervals.size() > 0)
    ret = m_intervals[0].get_min();
  else
    throw std::runtime_error("requested min for empty set");
  return ret;
}

template<class T>
T Set<T>::get_max() const {
  T ret;
  if (m_intervals.size() > 0)
    ret = m_intervals[0].get_max();
  else
    throw std::runtime_error("requested max for empty set");
  return ret;
}

template<class T> bool
Set<T>::operator==(const Set<T>& rhs) const {
  return m_intervals == rhs.get_intervals();
}

template<class T> bool
Set<T>::operator!=(const Set<T>& rhs) const {
  return !(*this == rhs);
}

template<typename T> std::ostream&
operator<<(std::ostream& os, const Set<T>& rhs) {
  if (rhs.get_is_empty() || (rhs.get_intervals().size() != 1))
    os << "{"; // set start
  if (!rhs.get_is_empty()) {
    auto it = rhs.get_intervals().begin(); 
    for (; it != rhs.get_intervals().end(); ++it) {
      os << *it;
      if (it+1 != rhs.get_intervals().end()) {
        os << ","; // interval separator
      }
    }
  }
  if (rhs.get_is_empty() || (rhs.get_intervals().size() != 1))
    os << "}"; // set end
  return os;
}

/// @brief https://en.wikipedia.org/wiki/Union_(set_theory)
template<typename T> Set<T>
union_of(const _Interval<T>& first, const _Interval<T>& second) {
  return union_of(Set<T>(first), second);
}

/// @brief https://en.wikipedia.org/wiki/Union_(set_theory)
template<typename T> Set<T>
union_of(const Set<T>& set, const _Interval<T>& interval) {
  bool do_append = true;
  std::vector<_Interval<T> > set_intervals = set.get_intervals();
  for (auto it = set_intervals.begin(); it != set_intervals.end(); ++it) {
    if (interval.get_min() > it->get_max()) {
      // interval                                     *****
      // *it                     ********************
      continue;
    }
    else { // (interval.get_min() <= it->get_max())
      if (interval.get_max() < it->get_min()) {
        // interval       ******
        // *it                     ********************
        set_intervals.insert(it, interval);
        do_append = false;
        break;
      }
      else { // (interval.get_max() >= it->get_min())
        if (interval.get_max() <= it->get_max()) {
          if (interval.get_min() < it->get_min()) {
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
          if (interval.get_min() <= it->get_min()) {
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
            if (it->get_max() < to_end->get_min()) {
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
  if (do_append) {
    // if this point is reached, it means interval is higher than any
    // other existing set_intervals so it must be appended
    set_intervals.push_back(interval);
  }
  return Set<T>(set_intervals);
}

/// @brief https://en.wikipedia.org/wiki/Intersection_(set_theory)
template<typename T> Set<T>
intersection_of(const _Interval<T>& first, const _Interval<T>& second) {
  std::vector<_Interval<T> > set_intervals;
  if (second.get_max() >= first.get_min()) {
    T min = first.get_min();
    if (second.get_min() > min)
      min = second.get_min();
    T max = first.get_max();
    if (second.get_max() < max)
      max = second.get_max();
    _Interval<T> interval(min, max);;
    set_intervals.push_back(interval);
  }
  auto ret = Set<T>(set_intervals);
  if (first.get_is_empty())
    ret.set_is_empty(true);
  if (second.get_is_empty())
    ret.set_is_empty(true);
  return ret;
}

/// @brief https://en.wikipedia.org/wiki/Intersection_(set_theory)
template<typename T> Set<T>
intersection_of(const Set<T>& set, const _Interval<T>& interval) {
  std::vector<_Interval<T> > set_intervals = set.get_intervals();
  auto it = set_intervals.begin();
  while(it != set_intervals.end()) {
    T iv_min = interval.get_min();
    T iv_max = interval.get_max();
    if ((iv_max < it->get_min()) || (iv_min > it->get_max()))
      it = set_intervals.erase(it);
    else {
      bool override_min = false;
      bool override_max = false;
      if ((iv_min > it->get_min()) && (iv_min <= it->get_max())) {
        override_min = true;
      }
      if ((iv_max >= it->get_min()) && (iv_max <= it->get_max())) {
        override_max = true;
      }
      if (override_min)
        it->set_min(iv_min);
      if (override_max)
        it->set_max(iv_max);
      it++;
    }
  }
  return Set<T>(set_intervals);
}

CSPSolver::Constr::Constr() :
    Func("", "", ""),
    m_rhs_int32_const(0),
    m_rhs_double_const(0),
    m_rhs_is_var(false),
    m_rhs_is_int32_const(false),
    m_rhs_is_double_const(false) {
}

CSPSolver::Constr::Constr(const std::string& lhs, const std::string& type,
    const int32_t rhs) : Func(lhs, type, ""),
    m_rhs_int32_const(rhs),
    m_rhs_double_const(0),
    m_rhs_is_var(false),
    m_rhs_is_int32_const(true),
    m_rhs_is_double_const(false) {
  throw_invalid_argument_if_constraint_not_supported();
}

CSPSolver::Constr::Constr(const std::string& lhs, const std::string& type,
    const double rhs) : Func(lhs, type, ""),
    m_rhs_int32_const(0),
    m_rhs_double_const(rhs),
    m_rhs_is_var(false),
    m_rhs_is_int32_const(false),
    m_rhs_is_double_const(true) {
  throw_invalid_argument_if_constraint_not_supported();
}

CSPSolver::Constr::Constr(const std::string& lhs, const std::string& type,
    const std::string& rhs) : Func(lhs, type, rhs),
    m_rhs_int32_const(0),
    m_rhs_double_const(0),
    m_rhs_is_var(true),
    m_rhs_is_int32_const(false),
    m_rhs_is_double_const(false) {
  throw_invalid_argument_if_constraint_not_supported();
}

void CSPSolver::Constr::
    throw_invalid_argument_if_constraint_not_supported() {
  bool constraint_is_supported = false;
  constraint_is_supported |= (std::string(m_type) == ">=");
  constraint_is_supported |= (std::string(m_type) == ">");
  constraint_is_supported |= (std::string(m_type) == "<=");
  constraint_is_supported |= (std::string(m_type) == "<");
  constraint_is_supported |= (std::string(m_type) == "=");
  if (!constraint_is_supported) {
    std::ostringstream oss;
    oss << "invalid constraint specified: " << m_type;
    throw std::invalid_argument(oss.str());
  }
}

bool
CSPSolver::FeasibleRegionLimits::Var::contains(_Interval<int32_t> interval) {
  bool ret = false;
  if (m_type_is_int32) {
    ret = intersection_of(m_int32_set, interval).get_intervals().size() > 0;
  }
  else {
    _Interval<double> iv_double(interval);
    ret = intersection_of(m_double_set, iv_double).get_intervals().size() > 0;
  }
  return ret;
}

bool
CSPSolver::FeasibleRegionLimits::Var::contains(_Interval<double> interval) {
  bool ret = false;
  if (m_type_is_int32)
    throw std::runtime_error("requested invalid int32 contains double");
  else
    ret = intersection_of(m_double_set, interval).get_intervals().size() > 0;
  //std::cout << m_double_set << "\n";
  return ret;
}

bool
CSPSolver::FeasibleRegionLimits::Var::get_is_empty() {
  bool ret;
  if (m_type_is_int32)
    ret = m_int32_set.get_is_empty();
  else
    ret = m_double_set.get_is_empty();
  return ret;
}

_Interval<int32_t>
CSPSolver::FeasibleRegionLimits::get_int32_interval_limits() {
  int32_t max = std::numeric_limits<int32_t>::max();
  int32_t min = std::numeric_limits<int32_t>::min();
  return _Interval<int32_t>(min, max);
}

_Interval<double>
CSPSolver::FeasibleRegionLimits::get_double_interval_limits(double tol) {
  double max = std::numeric_limits<double>::max();
  double min = -max;
  return _Interval<double>(min, max, tol);
}

void
CSPSolver::FeasibleRegionLimits::set_var_limits_to_universal_set(
    std::pair<const std::string,FeasibleRegionLimits::Var>& var) {
  if (var.second.m_type_is_int32) {
    var.second.m_int32_set = Set<int32_t>(get_int32_interval_limits());
  }
  else {
    double tol = var.second.m_fp_comparison_tol;
    var.second.m_double_set = Set<double>(get_double_interval_limits(tol));
  }
}

void
CSPSolver::FeasibleRegionLimits::set_var_limits_to_empty_set(
    std::pair<const std::string,FeasibleRegionLimits::Var>& var) {
  if (var.second.m_type_is_int32)
    var.second.m_int32_set.set_is_empty(true);
  else
    var.second.m_double_set.set_is_empty(true);
}

bool
CSPSolver::FeasibleRegionLimits::operator==(
    const CSPSolver::FeasibleRegionLimits& rhs) const {
  bool ret = true;
  for (auto it = m_vars.begin(); it != m_vars.end(); ++it) {
    auto itrhs = rhs.m_vars.begin();
    for (; itrhs != rhs.m_vars.end(); ++itrhs) {
      if (it->first == itrhs->first) { // if var key matches
        if (it->second.m_type_is_int32 != itrhs->second.m_type_is_int32) {
          ret = false;
          break;
        }
        if (it->second.m_type_is_int32) {
          if (it->second.m_int32_set != itrhs->second.m_int32_set ) {
            ret = false;
            break;
          }
        }
        else {
          if (it->second.m_double_set != itrhs->second.m_double_set) {
            ret = false;
            break;
          }
        }
      }
    }
    if (ret == false)
      break;
  }
  return ret;
}

bool
CSPSolver::FeasibleRegionLimits::operator!=(
    const CSPSolver::FeasibleRegionLimits& rhs) const {
  return !(*this == rhs);
}

std::ostream&
operator<<(std::ostream& os, const CSPSolver::FeasibleRegionLimits::Var& var) {
  if (var.m_type_is_int32)
    os << var.m_int32_set;
  else
    os << var.m_double_set;
  return os;
}

std::ostream&
operator<<(std::ostream& os, const CSPSolver::FeasibleRegionLimits& rhs) {
  bool first = true;
  os << "<";
  for (auto it = rhs.m_vars.begin(); it != rhs.m_vars.end(); ++it) {
    if (!first)
      os << ",";
    first = false;
    os << it->first << ":" << it->second;
  }
  os << ">";
  return os;
}

CSPSolver::CSPSolver(size_t max_num_constr_prop_loop_iter) :
    m_max_num_constr_prop_loop_iter(max_num_constr_prop_loop_iter),
    m_constr_max_id(0) {
}

template<> void
CSPSolver::add_var<int32_t> (const std::string& var_key) {
  int32_t hi = std::numeric_limits<int32_t>::max();
  int32_t lo = std::numeric_limits<int32_t>::min();
  typedef FeasibleRegionLimits::Var Var;
  m_feasible_region_limits.m_vars.insert(std::make_pair(var_key, Var(lo, hi)));
}

template<> void
CSPSolver::add_var<double> (const std::string& var_key,
    double fp_comparison_tol) {
  double hi = std::numeric_limits<double>::max();
  double lo = -hi;
  typedef FeasibleRegionLimits::Var Var;
  double tol = fp_comparison_tol;
  const std::string& key = var_key;
  m_feasible_region_limits.m_vars.insert(std::make_pair(key, Var(lo, hi, tol)));
}

template<typename T> size_t
CSPSolver::add_constr(const std::string& lhs, const std::string& type,
    const T& rhs) {
  throw_invalid_argument_if_var_key_has_not_been_added(lhs);
  m_constr[m_constr_max_id] = Constr(lhs, type, rhs);
  propagate_constraints();
  /// @todo / FIXME - this is unbounded... investigate better solution
  return m_constr_max_id++;
}

void
CSPSolver::remove_constr(size_t id) {
  m_constr.erase(id);
  if (id == m_constr_max_id-1)
    m_constr_max_id--;
  propagate_constraints();
  //std::cout << "solver is now: " << *this << "\n";
}

const CSPSolver::FeasibleRegionLimits&
CSPSolver::get_feasible_region_limits() const {
  return m_feasible_region_limits;
}

const std::map<size_t,CSPSolver::Constr>&
CSPSolver::get_constr() const {
  return m_constr;
}

bool
CSPSolver::feasible_region_limits_is_empty_for_var(
    const std::string& var) const {
  bool ret;
  auto lims = m_feasible_region_limits.m_vars.at(var);
  if (lims.m_type_is_int32)
    ret = lims.m_int32_set.get_is_empty();
  else
    ret = lims.m_double_set.get_is_empty();
  return ret;
}

const CSPSolver::FeasibleRegionLimits::Var&
CSPSolver::get_feasible_region_limits(const std::string& var) const {
  return m_feasible_region_limits.m_vars.at(var);
}

/// @return minimum as a double, regardless of whether var is an int32 or not
double
CSPSolver::get_feasible_region_limits_min_double(const std::string& var) const {
  double ret;
  auto lims = m_feasible_region_limits.m_vars.at(var);
  if (lims.m_type_is_int32)
    ret = (double) lims.m_int32_set.get_min();
  else
    ret = lims.m_double_set.get_min();
  return ret;
}

bool
CSPSolver::get_var_has_been_added(const std::string& var_key) const {
  const FeasibleRegionLimits& limits = m_feasible_region_limits;
  return limits.m_vars.find(var_key) != limits.m_vars.end();
}

template<typename T> bool
CSPSolver::val_is_within_var_feasible_region(T val,
    const std::string& var_key) const {
  bool ret = false;
  auto lims = m_feasible_region_limits.m_vars.at(var_key);
  if (lims.m_type_is_int32) {
    auto& intervals = lims.m_int32_set.get_intervals();
    for (auto it = intervals.begin(); it != intervals.end(); ++it)
      if (it->is_superset_of(val)) {
        ret = true;
        break;
      }
  }
  else {
    auto& intervals = lims.m_double_set.get_intervals();
    for (auto it = intervals.begin(); it != intervals.end(); ++it)
      if (it->is_superset_of(val)) {
        ret = true;
        break;
      }
  }
  return ret;
}

_Interval<int32_t>
CSPSolver::get_interval_for_constr(Constr constr) {
  int32_t min, max;
  if (std::string(constr.m_type) == ">=") {
    min = constr.m_rhs_int32_const;
    max = std::numeric_limits<int32_t>::max();
  }
  else if (std::string(constr.m_type) == ">") {
    min = constr.m_rhs_int32_const+1;
    max = std::numeric_limits<int32_t>::max();
  }
  else if (std::string(constr.m_type) == "<=") {
    min = std::numeric_limits<int32_t>::min();
    max = constr.m_rhs_int32_const;
  }
  else if (std::string(constr.m_type) == "<") {
    min = std::numeric_limits<int32_t>::min();
    max = constr.m_rhs_int32_const-1;
  }
  else if (std::string(constr.m_type) == "=") {
    min = constr.m_rhs_int32_const;
    max = constr.m_rhs_int32_const;
  }
  return _Interval<int32_t>(min, max);
}

_Interval<double>
CSPSolver::get_interval_for_constr(Constr constr, double tol) {
  double min, max;
  if (std::string(constr.m_type) == ">=") {
    min = constr.m_rhs_double_const;
    max = std::numeric_limits<double>::max();
  }
  else if (std::string(constr.m_type) == ">") {
    /// @todo/FIXME - add unit test for replacement of below line
    //min = constr.m_rhs_double_const+(-DBL_MAX);
    min = constr.m_rhs_double_const+FLT_MIN;
    max = std::numeric_limits<double>::max();
  }
  else if (std::string(constr.m_type) == "<=") {
    min = -std::numeric_limits<double>::max();
    max = constr.m_rhs_double_const;
  }
  else if (std::string(constr.m_type) == "<") {
    min = -std::numeric_limits<double>::max();
    /// @todo/FIXME - add unit test for replacement of below line
    //max = constr.m_rhs_double_const-(-DBL_MAX);
    max = constr.m_rhs_double_const-FLT_MIN;
  }
  else if (std::string(constr.m_type) == "=") {
    min = constr.m_rhs_double_const;
    max = constr.m_rhs_double_const;
  }
  return _Interval<double>(min, max, tol);
}

void
CSPSolver::assign_var_to_intersection_of_var_and_interval(
    std::pair<const std::string,FeasibleRegionLimits::Var>& var,
    _Interval<int32_t>& iv) {
  var.second.m_int32_set = intersection_of(var.second.m_int32_set, iv);
}

void
CSPSolver::assign_var_to_intersection_of_var_and_interval(
    std::pair<const std::string,FeasibleRegionLimits::Var>& var,
    _Interval<double>& iv) {
  var.second.m_double_set = intersection_of(var.second.m_double_set, iv);
}

void
CSPSolver::propagate_constr_rhs_const(
    std::pair<const std::string,FeasibleRegionLimits::Var>& ivar,
    Constr& constr) {
  Set<int32_t> cc_set_int32;
  Set<double> cc_set_double;
  if (ivar.second.m_type_is_int32) {
    assign_set_to_universal_set(cc_set_int32, 0);
  }
  else {
    auto& tol = ivar.second.m_fp_comparison_tol;
    assign_set_to_universal_set(cc_set_double, tol);
  }
  if (ivar.second.m_type_is_int32) {
    // forward interval
    _Interval<int32_t> ivf = get_interval_for_constr(constr);
    // forward constraint
    assign_var_to_intersection_of_var_and_interval(ivar, ivf);
  }
  else {
    // forward interval
    double tol = ivar.second.m_fp_comparison_tol;
    _Interval<double> ivf = get_interval_for_constr(constr, tol);
    // forward constraint
    assign_var_to_intersection_of_var_and_interval(ivar, ivf);
  }
}

void
CSPSolver::propagate_constr_rhs_var(
    std::pair<const std::string, FeasibleRegionLimits::Var>& ivar,
    Constr& constr) {
  auto& vars = m_feasible_region_limits.m_vars;
  auto& rhs = vars.at(constr.m_rhs);
  // forward constraint (constrain the lhs var by the rhs var)
  if (!rhs.m_type_is_int32) {
    double min, max;
    auto& set = rhs.m_double_set; // rhs set
    if (set.get_is_empty()) {
      ivar.second.m_double_set.set_is_empty(true);
    }
    else {
      if (std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<double>::max();
      }
      else if (std::string(constr.m_type) == ">") {
        min = set.get_min()+(-DBL_MAX);
        max = std::numeric_limits<double>::max();
      }
      else if (std::string(constr.m_type) == "<=") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max();
      }
      else if (std::string(constr.m_type) == "<") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max()-(-DBL_MAX);
      }
      else if (std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      auto& lhs_set = ivar.second.m_double_set;
      // forward interval
      _Interval<double> iv(min, max, ivar.second.m_fp_comparison_tol);
      //std::cout << "forward constraint: intersecting " << ivar.first;
      //std::cout << " with " << iv << "\n";
      lhs_set = intersection_of(lhs_set, iv);
    }
  }
  else {
    int32_t min, max;
    auto& set = rhs.m_int32_set; // rhs set
    if (set.get_is_empty()) {
      ivar.second.m_int32_set.set_is_empty(true);
    }
    else {
      if (std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<int32_t>::max();
      }
      else if (std::string(constr.m_type) == ">") {
        min = set.get_min()+1;
        max = std::numeric_limits<int32_t>::max();
      }
      else if (std::string(constr.m_type) == "<=") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max();
      }
      else if (std::string(constr.m_type) == "<") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max()-1;
      }
      else if (std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      auto& lhs_set = ivar.second.m_int32_set;
      _Interval<int32_t> iv(min, max); // forward interval
      lhs_set = intersection_of(lhs_set, iv);
    }
  }
  // reverse constraint (constrain the rhs var by the lhs var)
  if (!ivar.second.m_type_is_int32) {
    double min, max;
    auto& set = ivar.second.m_double_set; // lhs set
    if (set.get_is_empty()) {
      rhs.m_double_set.set_is_empty(true);
    }
    else {
      if (std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<double>::max();
      }
      else if (std::string(constr.m_type) == ">") {
        min = set.get_min()+(-DBL_MAX);
        max = std::numeric_limits<double>::max();
      }
      else if (std::string(constr.m_type) == "<=") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max();
      }
      else if (std::string(constr.m_type) == "<") {
        min = -std::numeric_limits<double>::max();
        max = set.get_max()-(-DBL_MAX);
      }
      else if (std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      // reverse interval
      _Interval<double> iv(min, max, ivar.second.m_fp_comparison_tol);
      auto& rhs_set = rhs.m_double_set;
      //std::cout << "reverse constraint: intersecting " << constr.m_rhs;
      //std::cout << " with " << iv << "\n";
      rhs_set = intersection_of(rhs_set, iv);
    }
  }
  else {
    int32_t min, max;
    auto& set = ivar.second.m_int32_set; // lhs set
    if (set.get_is_empty()) {
      rhs.m_int32_set.set_is_empty(true);
    }
    else {
      if (std::string(constr.m_type) == ">=") {
        min = set.get_min();
        max = std::numeric_limits<int32_t>::max();
      }
      else if (std::string(constr.m_type) == ">") {
        min = set.get_min()+1;
        max = std::numeric_limits<int32_t>::max();
      }
      else if (std::string(constr.m_type) == "<=") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max();
      }
      else if (std::string(constr.m_type) == "<") {
        min = std::numeric_limits<int32_t>::min();
        max = set.get_max()-1;
      }
      else if (std::string(constr.m_type) == "=") {
        min = set.get_min();
        max = set.get_max();
      }
      _Interval<int32_t> iv(min, max); // reverse interval
      auto& rhs_set = rhs.m_int32_set;
      rhs_set = intersection_of(rhs_set, iv);
    }
  }
}

/// @brief https://en.wikipedia.org/wiki/Universal_set
/// @todo / FIXME - remove tol??
void
CSPSolver::assign_set_to_universal_set(Set<int32_t>& set, int32_t /*tol*/) {
  int32_t max = std::numeric_limits<int32_t>::max();
  int32_t min = std::numeric_limits<int32_t>::min();
  _Interval<int32_t> interval(min, max);
  set = Set<int32_t>(interval);
}

/// @brief https://en.wikipedia.org/wiki/Universal_set
void
CSPSolver::assign_set_to_universal_set(Set<double>& set, double tol) {
  double max = std::numeric_limits<double>::max();
  double min = -max;
  _Interval<double> interval(min, max, tol);
  set = Set<double>(interval);
}

/// @brief https://en.wikipedia.org/wiki/Constraint_propagation
void
CSPSolver::propagate_constraints() {
  auto _itvs = m_feasible_region_limits.m_vars.begin();
  for (; _itvs != m_feasible_region_limits.m_vars.end(); ++_itvs)
    m_feasible_region_limits.set_var_limits_to_universal_set(*_itvs);
  bool pending_iter = true;
  /// @todo / FIXME - ensure developers can override value of max_num...iter
  for (size_t iter=1; iter <= m_max_num_constr_prop_loop_iter; iter++) {
    FeasibleRegionLimits limits_from_prev_iter = m_feasible_region_limits;
    // variable_loop: (iterate over all variables (X))
    auto itvs = m_feasible_region_limits.m_vars.begin(); 
    for (; itvs != m_feasible_region_limits.m_vars.end(); ++itvs) {
      for (size_t count=1; count<=2; count++) {
        // iterate over all constraints (C)
        for (auto itcs = m_constr.begin(); itcs != m_constr.end(); itcs++) {
          // if constraint is applied to current_var
          if (itcs->second.m_lhs == itvs->first) {
            if (count == 1 && itcs->second.m_rhs_is_int32_const)
              propagate_constr_rhs_const(*itvs, itcs->second);
            else if (count == 1 && itcs->second.m_rhs_is_double_const)
              propagate_constr_rhs_const(*itvs, itcs->second);
            else if (count == 2 && itcs->second.m_rhs_is_var)
              propagate_constr_rhs_var(  *itvs, itcs->second);
          }
        }
      }
    }
    if (m_feasible_region_limits == limits_from_prev_iter) {
      pending_iter = false;
      break;
    }
  }
  if (pending_iter)
    throw std::runtime_error("erroneous state propagation loops exceeded");
}

void
CSPSolver::throw_invalid_argument_if_var_key_has_not_been_added(
    const std::string& var_key) {
  if (!get_var_has_been_added(var_key)) {
    std::ostringstream oss;
    oss << "invalid constraint specified (variable " << var_key;
    oss << " has not been added)";
    throw std::invalid_argument(oss.str());
  }
}
