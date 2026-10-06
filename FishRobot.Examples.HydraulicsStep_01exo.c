/* External objects file */
#include "FishRobot.Examples.HydraulicsStep_model.h"
#if defined(__cplusplus)
extern "C" {
#endif

void FishRobot_Examples_HydraulicsStep_callExternalObjectDestructors(DATA *data, threadData_t *threadData)
{
  if(data->simulationInfo->extObjs)
  {
    omc_Modelica_Blocks_Types_ExternalCombiTimeTable_destructor(threadData,(data->simulationInfo->extObjs[2]));
    omc_Modelica_Blocks_Types_ExternalCombiTable1D_destructor(threadData,(data->simulationInfo->extObjs[0]));
    omc_Modelica_Blocks_Types_ExternalCombiTable1D_destructor(threadData,(data->simulationInfo->extObjs[1]));
    free(data->simulationInfo->extObjs);
    data->simulationInfo->extObjs = 0;
  }
}
#if defined(__cplusplus)
}
#endif
