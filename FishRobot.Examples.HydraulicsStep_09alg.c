/* Algebraic */
#include "FishRobot.Examples.HydraulicsStep_model.h"

#ifdef __cplusplus
extern "C" {
#endif

/* forwarded equations */
extern void FishRobot_Examples_HydraulicsStep_eqFunction_104(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_105(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_106(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_107(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_108(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_110(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_114(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_124(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_129(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_134(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_136(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_137(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_170(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_171(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_172(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_173(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_174(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_177(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_179(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_181(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_185(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_186(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_187(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_188(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_189(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_190(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_192(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_194(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_195(DATA* data, threadData_t *threadData);

static void functionAlg_system0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[29])(DATA*, threadData_t*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_104,
    FishRobot_Examples_HydraulicsStep_eqFunction_105,
    FishRobot_Examples_HydraulicsStep_eqFunction_106,
    FishRobot_Examples_HydraulicsStep_eqFunction_107,
    FishRobot_Examples_HydraulicsStep_eqFunction_108,
    FishRobot_Examples_HydraulicsStep_eqFunction_110,
    FishRobot_Examples_HydraulicsStep_eqFunction_114,
    FishRobot_Examples_HydraulicsStep_eqFunction_124,
    FishRobot_Examples_HydraulicsStep_eqFunction_129,
    FishRobot_Examples_HydraulicsStep_eqFunction_134,
    FishRobot_Examples_HydraulicsStep_eqFunction_136,
    FishRobot_Examples_HydraulicsStep_eqFunction_137,
    FishRobot_Examples_HydraulicsStep_eqFunction_170,
    FishRobot_Examples_HydraulicsStep_eqFunction_171,
    FishRobot_Examples_HydraulicsStep_eqFunction_172,
    FishRobot_Examples_HydraulicsStep_eqFunction_173,
    FishRobot_Examples_HydraulicsStep_eqFunction_174,
    FishRobot_Examples_HydraulicsStep_eqFunction_177,
    FishRobot_Examples_HydraulicsStep_eqFunction_179,
    FishRobot_Examples_HydraulicsStep_eqFunction_181,
    FishRobot_Examples_HydraulicsStep_eqFunction_185,
    FishRobot_Examples_HydraulicsStep_eqFunction_186,
    FishRobot_Examples_HydraulicsStep_eqFunction_187,
    FishRobot_Examples_HydraulicsStep_eqFunction_188,
    FishRobot_Examples_HydraulicsStep_eqFunction_189,
    FishRobot_Examples_HydraulicsStep_eqFunction_190,
    FishRobot_Examples_HydraulicsStep_eqFunction_192,
    FishRobot_Examples_HydraulicsStep_eqFunction_194,
    FishRobot_Examples_HydraulicsStep_eqFunction_195
  };
  
  if (data->simulationInfo->evalSelection) {
    for (int i = 0; i < data->simulationInfo->evalSelection->n; i++) {
      int id = data->simulationInfo->evalSelection->idx[i];
      eqFunctions[id](data, threadData);
    }
  } else {
    for (int id = 0; id < 29; id++) {
      eqFunctions[id](data, threadData);
    }
  }
}
/* for continuous time variables */
int FishRobot_Examples_HydraulicsStep_functionAlgebraics(DATA *data, threadData_t *threadData)
{

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_ALGEBRAICS);
#endif
  data->simulationInfo->callStatistics.functionAlgebraics++;

  FishRobot_Examples_HydraulicsStep_function_savePreSynchronous(data, threadData);
  
  functionAlg_system0(data, threadData);

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_ALGEBRAICS);
#endif

  return 0;
}

#ifdef __cplusplus
}
#endif
