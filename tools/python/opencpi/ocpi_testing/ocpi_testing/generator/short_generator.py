#!/usr/bin/env python3

# Class for generating short sample input data
#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import math
import random

from . import base_generator


class ShortGeneratorDefaults:
    # This class houses all the default values used. The structure is designed
    # for importing and documenting in an easier way.

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: Number of samples in a sample message for the message size test case and
    #: longest test subcase.
    MESSAGE_SIZE_LONGEST = 8192

    #: Minimum value a short number allows.
    SHORT_MINIMUM = -(2**15)

    #: Maximum value a short number allows.
    SHORT_MAXIMUM = 2**15 - 1

    #: Mean of the Gaussian probability distribution function of the random
    #: number generator used to set the amplitude of the sinusoidal waves that
    #: are combined in a sample message for the typical test case.
    TYPICAL_AMPLITUDE_MEAN = SHORT_MAXIMUM // 2

    #: Width of the Gaussian probability distribution function of the random
    #: number generator used to set the amplitude of the sinusoidal waves that
    #: are combined in a sample message for the typical test case.
    TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH = SHORT_MAXIMUM // 4

    #: Maximum amplitude of the sinusoidal waves that are combined in a sample
    #: message for typical test case.
    TYPICAL_MAXIMUM_AMPLITUDE = (
        SHORT_MAXIMUM * base_generator.GeneratorDefaults.LIMITED_SCALE_FACTOR)


class ShortGenerator(base_generator.BaseGenerator):
    """ Short protocol test data generator
    """

    def __init__(self):
        """ Initialise short generator class

        Defines the default values for the variables that control the values
        and size of messages that are generated.

        Returns:
            An initialised ShortGenerator instance.
        """
        super().__init__()

        # Set variables as local as may be modified when set in the specific
        # generator. Keep the same variable names to ensure documentation
        # matches.
        self.MESSAGE_SIZE_LONGEST = ShortGeneratorDefaults.MESSAGE_SIZE_LONGEST
        self.SHORT_MINIMUM = ShortGeneratorDefaults.SHORT_MINIMUM
        self.SHORT_MAXIMUM = ShortGeneratorDefaults.SHORT_MAXIMUM
        self.TYPICAL_AMPLITUDE_MEAN = \
            ShortGeneratorDefaults.TYPICAL_AMPLITUDE_MEAN
        self.TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH = \
            ShortGeneratorDefaults.TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH
        self.TYPICAL_MAXIMUM_AMPLITUDE = \
            ShortGeneratorDefaults.TYPICAL_MAXIMUM_AMPLITUDE

    def typical(self, seed, subcase):
        """ Generate a sample message with typical data inputs

        Combine a number of sinusoidal waves together, so that the output is
        the superposition of several sinusoidal waves.

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the typical case and the stated subcase.
        """
        random.seed(seed)

        # Use log normal distribution to get a bias towards more waves than the
        # modal
        number_of_waves = int(random.lognormvariate(
            math.log(self.TYPICAL_NUMBER_OF_WAVES_MODAL),
            math.log(self.TYPICAL_NUMBER_OF_WAVES_DISTRIBUTION_WIDTH)))
        if number_of_waves < self.TYPICAL_NUMBER_OF_WAVES_MIN:
            number_of_waves = self.TYPICAL_NUMBER_OF_WAVES_MIN
        if number_of_waves > self.TYPICAL_NUMBER_OF_WAVES_MAX:
            number_of_waves = self.TYPICAL_NUMBER_OF_WAVES_MAX

        frequencies = [0] * number_of_waves
        phases = [0] * number_of_waves
        amplitudes = [0] * number_of_waves

        for wave in range(number_of_waves):
            frequencies[wave] = random.gauss(
                self.TYPICAL_FREQUENCY_MEAN,
                self.TYPICAL_FREQUENCY_DISTRIBUTION_WIDTH)
            if frequencies[wave] < self.TYPICAL_FREQUENCY_MIN:
                frequencies[wave] = self.TYPICAL_FREQUENCY_MIN
            if frequencies[wave] > self.TYPICAL_FREQUENCY_MAX:
                frequencies[wave] = self.TYPICAL_FREQUENCY_MAX

            phases[wave] = random.uniform(0, 2 * math.pi)

            amplitudes[wave] = abs(random.gauss(
                self.TYPICAL_AMPLITUDE_MEAN / number_of_waves,
                self.TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH))

        # Scale amplitude if maximum is exceeded
        amplitude_sum = sum(amplitudes)
        if amplitude_sum > self.TYPICAL_MAXIMUM_AMPLITUDE:
            scale_factor = self.TYPICAL_MAXIMUM_AMPLITUDE / amplitude_sum
            amplitudes = [amplitude * scale_factor for amplitude in amplitudes]

        data = [0] * self.SAMPLE_DATA_LENGTH
        for index in range(len(data)):
            for frequency, phase, amplitude in zip(
                    frequencies, phases, amplitudes):
                data[index] = data[index] + int(
                    amplitude * math.cos(2 * math.pi * frequency * index +
                                         phase))

        return [{"opcode": "sample", "data": data}]

    def sample(self, seed, subcase):
        """ Generate sample messages to test different supported values

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the typical case and the stated subcase.
        """
        random.seed(seed)
        if subcase == "all_zero":
            return [{"opcode": "sample",
                     "data": [0] * self.SAMPLE_DATA_LENGTH}]

        elif subcase == "all_maximum":
            return [{"opcode": "sample",
                     "data": [self.SHORT_MAXIMUM] * self.SAMPLE_DATA_LENGTH}]

        elif subcase == "all_minimum":
            return [{"opcode": "sample",
                     "data": [self.SHORT_MINIMUM] * self.SAMPLE_DATA_LENGTH}]

        elif subcase == "large_positive":
            data = [0] * self.SAMPLE_DATA_LENGTH
            for index in range(self.SAMPLE_DATA_LENGTH):
                data[index] = random.randint(
                    self.SHORT_MAXIMUM - self.SAMPLE_NEAR_RANGE,
                    self.SHORT_MAXIMUM)
            return [{"opcode": "sample", "data": data}]

        elif subcase == "large_negative":
            data = [0] * self.SAMPLE_DATA_LENGTH
            for index in range(self.SAMPLE_DATA_LENGTH):
                data[index] = random.randint(
                    self.SHORT_MINIMUM,
                    self.SHORT_MINIMUM + self.SAMPLE_NEAR_RANGE)
            return [{"opcode": "sample", "data": data}]

        elif subcase == "near_zero":
            data = [0] * self.SAMPLE_DATA_LENGTH
            for index in range(self.SAMPLE_DATA_LENGTH):
                data[index] = random.randint(-self.SAMPLE_NEAR_RANGE,
                                             self.SAMPLE_NEAR_RANGE)
            return [{"opcode": "sample", "data": data}]

        else:
            raise ValueError(f"Unexpected subcase of {subcase} for sample()")

    def sample_other_port(self, seed, subcase):
        """ Messages when testing another port's handling of sample messages

        In all subcases generate some random data for the port.

        Usually called via ``self.generate()``.

        Args:
            seed (int): The seed value to use for random number generation.
            subcase (str): Name of the subcase messages are to be generated
                for.

        Returns:
            Messages for the typical case and the stated subcase.
        """
        random.seed(seed)
        return [{"opcode": "sample", "data": self._get_sample_values()}]

    def _full_scale_random_sample_values(self, number_of_samples=None):
        """ Generate a random sample of shorts

        Args:
            number_of_samples (int, optional): The number of random values to
                be generated. If not set will default to None, which means the
                number of samples defined by self.SAMPLE_DATA_LENGTH will be
                generated.

        Returns:
            List of the generated random values.
        """
        if number_of_samples is None:
            number_of_samples = self.SAMPLE_DATA_LENGTH

        data = [0] * number_of_samples
        for index in range(number_of_samples):
            data[index] = random.randint(self.SHORT_MINIMUM,
                                         self.SHORT_MAXIMUM)
        return data

    def _get_sample_values(self, number_of_samples=None):
        """ Generate a random sample of shorts

        The values generated are a subset of the whole supported range that
        shorts can represent, this range size is set by
        self.LIMITED_SCALE_FACTOR.

        Args:
            number_of_samples (int, optional): The number of random values to
                be generated. If not set will default to None, which means the
                number of samples defined by self.SAMPLE_DATA_LENGTH will be
                generated.

        Returns:
            List of the generated random values.
        """
        if number_of_samples is None:
            number_of_samples = self.SAMPLE_DATA_LENGTH

        limited_range_min = round(
            self.LIMITED_SCALE_FACTOR * self.SHORT_MINIMUM)
        limited_range_max = round(
            self.LIMITED_SCALE_FACTOR * self.SHORT_MAXIMUM)

        data = [0] * number_of_samples
        for index in range(number_of_samples):
            data[index] = random.randint(limited_range_min, limited_range_max)
        return data
