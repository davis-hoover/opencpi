#!/usr/bin/env python3

# Class for generating unsigned character sample input data
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


class UnsignedCharacterGeneratorDefaults:
    # This class houses all the default values used. The structure is designed
    # for importing and documenting in an easier way.

    # The : after the # of comments here ensures the comments are imported into
    # the build documentation.

    #: Number of samples in a sample message for the message size test case and
    #: longest test subcase.
    MESSAGE_SIZE_LONGEST = 16384

    #: Minimum value an unsigned character number allows.
    UNSIGNED_CHARACTER_MINIMUM = 0

    #: Maximum value an unsigned character number allows.
    UNSIGNED_CHARACTER_MAXIMUM = (2**8) - 1

    #: Mid point of the range of values supported by an unsigned character.
    UNSIGNED_CHARACTER_MID = UNSIGNED_CHARACTER_MAXIMUM // 2

    #: Mean of the Gaussian probability distribution function of the random
    #: number generator used to set the amplitude of the sinusoidal waves that
    #: are combined in a sample message for the typical test case.
    TYPICAL_AMPLITUDE_MEAN = UNSIGNED_CHARACTER_MAXIMUM // 2

    #: Width of the Gaussian probability distribution function of the random
    #: number generator used to set the amplitude of the sinusoidal waves that
    #: are combined in a sample message for the typical test case.
    TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH = UNSIGNED_CHARACTER_MAXIMUM // 4

    #: Maximum amplitude of the sinusoidal waves that are combined in a sample
    #: message for typical test case.
    TYPICAL_MAXIMUM_AMPLITUDE = (
        UNSIGNED_CHARACTER_MID *
        base_generator.GeneratorDefaults.LIMITED_SCALE_FACTOR)


class UnsignedCharacterGenerator(base_generator.BaseGenerator):
    """ Unsigned character protocol test data generator
    """

    def __init__(self):
        """ Initialise unsigned character generator class

        Defines the default values for the variables that control the values
        and size of messages that are generated.

        Returns:
            An initialised UnsignedCharacterGenerator instance.
        """
        super().__init__()

        # Set variables as local as may be modified when set in the specific
        # generator. Keep the same variable names to ensure documentation
        # matches.
        self.MESSAGE_SIZE_LONGEST = \
            UnsignedCharacterGeneratorDefaults.MESSAGE_SIZE_LONGEST
        self.UNSIGNED_CHARACTER_MINIMUM = \
            UnsignedCharacterGeneratorDefaults.UNSIGNED_CHARACTER_MINIMUM
        self.UNSIGNED_CHARACTER_MAXIMUM = \
            UnsignedCharacterGeneratorDefaults.UNSIGNED_CHARACTER_MAXIMUM
        self.UNSIGNED_CHARACTER_MID = \
            UnsignedCharacterGeneratorDefaults.UNSIGNED_CHARACTER_MID
        self.TYPICAL_AMPLITUDE_MEAN = \
            UnsignedCharacterGeneratorDefaults.TYPICAL_AMPLITUDE_MEAN
        # No good way to break below line which exceeds 80 characters, allowing
        # line which is too long to maintain readability.
        self.TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH = \
            UnsignedCharacterGeneratorDefaults.TYPICAL_AMPLITUDE_DISTRIBUTION_WIDTH
        self.TYPICAL_MAXIMUM_AMPLITUDE = \
            UnsignedCharacterGeneratorDefaults.TYPICAL_MAXIMUM_AMPLITUDE

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
                data[index] = data[index] + amplitude * math.cos(
                    2 * math.pi * frequency * index + phase)
            data[index] = int(data[index] + self.UNSIGNED_CHARACTER_MID)

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
            return [
                {"opcode": "sample",
                 "data": [self.UNSIGNED_CHARACTER_MAXIMUM] *
                 self.SAMPLE_DATA_LENGTH}]

        elif subcase == "large_positive":
            data = [0] * self.SAMPLE_DATA_LENGTH
            for index in range(self.SAMPLE_DATA_LENGTH):
                data[index] = random.randint(
                    self.UNSIGNED_CHARACTER_MAXIMUM - self.SAMPLE_NEAR_RANGE,
                    self.UNSIGNED_CHARACTER_MAXIMUM)
            return [{"opcode": "sample", "data": data}]

        elif subcase == "near_zero":
            data = [0] * self.SAMPLE_DATA_LENGTH
            for index in range(self.SAMPLE_DATA_LENGTH):
                data[index] = random.randint(0, self.SAMPLE_NEAR_RANGE)
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
        """ Generate a random sample of unsigned characters

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
            data[index] = random.randint(self.UNSIGNED_CHARACTER_MINIMUM,
                                         self.UNSIGNED_CHARACTER_MAXIMUM)
        return data

    def _get_sample_values(self, number_of_samples=None):
        """ Generate a random sample of unsigned characters

        The values generated are a subset of the whole supported range that
        unsigned characters can represent, this range size is set by
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
            self.LIMITED_SCALE_FACTOR * self.UNSIGNED_CHARACTER_MINIMUM)
        limited_range_max = round(
            self.LIMITED_SCALE_FACTOR * self.UNSIGNED_CHARACTER_MAXIMUM)

        data = [0] * number_of_samples
        for index in range(number_of_samples):
            data[index] = random.randint(limited_range_min, limited_range_max)
        return data
