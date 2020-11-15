/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Thu Jan  2 09:40:58 2020 CST
 * BASED ON THE FILE: cic_dec.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the cic_dec worker in C++
 */


// This file is based on the Python model and VHDL versions already implemented into OPENCPI
// To run the view script on the maximum test size, you need >16GB of RAM
// This implementation runs in three stages. The first reads in all of the input data. The second runs the CIC and Decimation algorithm.
// The third stage outputs all of the processed data.

#include "cic_dec-worker.hh"
#include <cmath>  // for use of log
#include <cstddef>
#include <cstdint>
#include <cstring>  // memcpy and memset
#include <queue>  // Used to toggle and for output comb
#include <vector>  // Needed for large size, and unknown variable length

using namespace OCPI::RCC;  // for easy access to RCC data types and constants
using namespace Cic_decWorkerTypes;
using std::queue;
using std::vector;
class Cic_decWorker : public Cic_decWorkerBase {

    queue<long> out_combI;
    queue<long> out_combQ;
    queue<bool> toggle1;
    queue<bool> toggle2;
    vector<short> *iData;  // can be very large, need to allocate to heap
    vector<short> *qData;
    RunCondition m_RunCondition;

    RCCResult initialize() {
        iData = new vector<short>;
        qData = new vector<short>;
        return RCC_OK;
    }

    RCCResult release() {
        delete iData;  // Delete allocated memory
        delete qData;
        iData = NULL;  // Throw error if attempted to use after
        qData = NULL;
        return RCC_OK;
    }
    RCCResult run(bool /*timedout*/) {

        if (!firstRun() && toggle1.empty())
        {
            in.advance();  // dont want to advance the port if its the first time
        }

        size_t num_of_elements = 0;
        IqstreamIqData *outData = out.iq().data().data();
        vector<long> out_decQ;
        vector<long> out_decI;

        if(toggle1.empty())  // stage 1 (input stage)
        {
            num_of_elements = in.iq().data().size();
            const IqstreamIqData *inData= in.iq().data().data();

            if (num_of_elements != 0)
            {
                for (size_t i = 0; i < num_of_elements; ++i)
                {
                    iData->push_back(inData->I);  // data into a vector so we can use it later.
                    qData->push_back(inData->Q);
                    ++inData;
                }
                return RCC_OK;
            }
        }

        if(toggle2.empty())
        {  // stage 2 (process stage)
            const int N = static_cast<int>(CIC_DEC_N);
            const int R = static_cast<int>(CIC_DEC_R);
            const int M = static_cast<int>(CIC_DEC_M);

            const int32_t ACC_WIDTH = ceil(N * log2(R * M))+ CIC_DEC_DIN_WIDTH;
            const int A = N+1;
            const int B = M+1;

            long comb_r[A];  // create combs
            long comb_dly[A][B];
            long comb[A];
            long comb_dly_r[A][B];
            memset(comb_r, 0, sizeof(comb_r));  // set to 0;
            memset(comb_dly, 0, sizeof(comb_dly[0][0]) * A * B);
            memset(comb, 0, sizeof(comb));
            memset(comb_dly_r, 0, sizeof(comb_dly_r[0][0]) * A * B);

            long integI[A];
            long integQ[A];
            long *out_integI = new long[iData->size()];  // can be massive
            long *out_integQ = new long[qData->size()];

            memset(integI, 0, sizeof(integI));
            memset(integQ, 0, sizeof(integQ));
            // Integrator

            long integPower = 1L << ACC_WIDTH;  // Calculate power of 2,ACC_width and return proper value;
            for (size_t i = 0; i < iData->size(); ++i)
            {
                integI[0] = iData->at(i);
                integQ[0] = qData->at(i);
                for (int j = 1; j < A ; ++j)
                {
                    integI[j] = integI[j] + integI[j-1];
                    integQ[j] = integQ[j] + integQ[j-1];
                    if (integI[j] > integPower)
                    {
                        integI[j] = integI[j]-integPower;
                    }
                    if (integQ[j] > integPower)
                    {
                        integQ[j] = integQ[j]-integPower;
                    }
                }
                out_integI[i] = integI[N];
                out_integQ[i] = integQ[N];
            }

            // Decimator
            for (unsigned int C = R-N; C < iData->size(); C+= R)
            {
                out_decI.push_back(out_integI[C]);
                out_decQ.push_back(out_integQ[C]);
            }

            int Y = out_decI.size();  // should be input length/R
            int Z = out_decQ.size();
            // comb section
            for(int i = 0; i < Y; ++i)
            {
                memcpy(comb_r, comb, sizeof(comb));
                memcpy(comb_dly_r, comb_dly, sizeof(comb_dly[0][0]) * A * B);
                comb[0] = out_decI.at(i);
                for(int j = 1; j< A; ++j )
                {
                    for(int k = 1; k< B; ++k)
                    {
                        comb_dly[j][k] = comb_dly_r[j][k-1];
                    }
                    comb_dly[j][0] = comb_r[j-1];
                    comb[j] = comb_r[j-1] - comb_dly[j][M];
                }
                out_combI.push(comb[N]);
            }

            memset(comb_r, 0, sizeof(comb_r));
            memset(comb_dly, 0, sizeof(comb_dly[0][0]) * A * B);
            memset(comb, 0, sizeof(comb));
            memset(comb_dly_r, 0, sizeof(comb_dly_r[0][0]) * A * B);  // reset combs

            for(int i = 0; i < Z; ++i)
            {
                memcpy(comb_r, comb, sizeof(comb));
                memcpy(comb_dly_r, comb_dly, sizeof(comb_dly[0][0]) * A * B);
                comb[0] = out_decQ.at(i);
                for(int j = 1; j < A ; ++j )
                {
                    for(int k = 1; k < B; ++k)
                    {
                        comb_dly[j][k] = comb_dly_r[j][k-1];
                    }
                    comb_dly[j][0] = comb_r[j-1];
                    comb[j] = comb_r[j-1] - comb_dly[j][M];
                }
                out_combQ.push(comb[N]);
            }
            delete [] out_integI;  // Delete allocated memory
            delete [] out_integQ;
            out_integI = NULL;
            out_integQ = NULL;
            toggle1.push(true);  // Unable to re-enter stage 1
            toggle2.push(true);  // Unable to re-enter stage 2

             // based on issue AV-4109
            m_RunCondition.setPortMasks(!in.hasBuffer()<<CIC_DEC_IN,out.hasBuffer()<<CIC_DEC_OUT,RCC_NO_PORTS);// Tell framework to call run even if no incoming data
            m_RunCondition.enableTimeout(1000); // 1ms TODO: Test to see if this part is necessary.
            setRunCondition(&m_RunCondition);
        }

        if(!toggle1.empty() && !toggle2.empty())  //start stage 3 (output stage)
        {

            const int N = static_cast<int>(CIC_DEC_N);
            const int R = static_cast<int>(CIC_DEC_R);
            const int M = static_cast<int>(CIC_DEC_M);
            const int32_t ACC_WIDTH = ceil(N * log2(R * M))+ CIC_DEC_DIN_WIDTH; //Repeated since they were out of scope

            size_t out_size = out_combQ.size();
            size_t outlength;
            if(out_size >= 512){
                outlength = 512;
            }
            else
            {
                outlength = out_size;
            }
            out.iq().data().resize(outlength);

            //for loop that advances outputbuffer maybe do size of out comb / R first.

            for(size_t j  = 0; j < outlength; ++j)
            {
                outData->I = (out_combI.front() >> (ACC_WIDTH - CIC_DEC_DIN_WIDTH));
                outData->Q = (out_combQ.front() >> (ACC_WIDTH - CIC_DEC_DIN_WIDTH));
                ++outData;
                out_combI.pop();
                out_combQ.pop();
            }

            if(!out_combI.empty())
            {
                out.advance();
                return RCC_OK;
            }
            else
            {
                out.advance();
                out.setEOF();
                setRunCondition(NULL);
                return RCC_ADVANCE_DONE;
            }
        }
        return RCC_OK;
    }
};

CIC_DEC_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
CIC_DEC_END_INFO
