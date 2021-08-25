/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Sat Aug 14 13:57:10 2021 EDT
 * BASED ON THE FILE: complex_mixer.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the complex_mixer worker in C++
 */
#include "complex_mixer-worker.hh"
#include <liquid/liquid.h>
#include <cmath>
#include <iostream>
#include <climits>

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Complex_mixerWorkerTypes;
using namespace std;

#define Uscale(x)  (float)((float)(x) / (pow(2,15) -1))
#define Scale(x)   (int16_t)((float)(x) * (pow(2,15) -1))

class Complex_mixerWorker : public Complex_mixerWorkerBase
{
  nco_crcf q;

  RCCResult initialize()
  {
    q = nco_crcf_create(LIQUID_NCO);
    nco_crcf_set_phase(q, 0.0f);

    return RCC_OK;
  }

  RCCResult release()
  {
    nco_crcf_destroy(q);

    return RCC_OK;
  }

  RCCResult run(bool /*timedout*/)
  {
    const IqstreamIqData* inData = in.iq().data().data();
    IqstreamIqData* outData = out.iq().data().data();
    const size_t num_of_elements = in.iq().data().size(); // size in IqstreamIqData units
    out.iq().data().resize(num_of_elements);

    // set each time so that if the container changes it gets updated
    // might be better to put this into a write sync function but this is for training
    float phase_inc = properties().phs_inc * ((2*M_PI)/(SHRT_MAX * 2));
    nco_crcf_set_frequency(q,phase_inc);

    liquid_float_complex out_sample;
    liquid_float_complex in_sample;

    for (unsigned int j = 0; j < num_of_elements; j++)
    {
      if (properties().enable)
      {
        in_sample.real = Uscale(inData->I);
        in_sample.imag = Uscale(inData->Q);
        nco_crcf_step(q);
        nco_crcf_mix_down(q, in_sample, &out_sample);
        outData->I = Scale(out_sample.real);
        outData->Q = Scale(out_sample.imag);

        inData++;
        outData++;
      }
      else
      {
        outData->I = inData->I;
        outData->Q = inData->Q;
        inData++;
        outData++;
      }
    }

    return num_of_elements ? RCC_ADVANCE : RCC_ADVANCE_DONE;
  }
};

COMPLEX_MIXER_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
COMPLEX_MIXER_END_INFO
