/* Asserts */
#include "FishRobot.Examples.HydraulicsStep_model.h"
#if defined(__cplusplus)
extern "C" {
#endif


/*
equation index: 357
type: ALGORITHM

  assert(pipeL.port_b.p >= 0.0, "Variable violating min constraint: 0.0 <= pipeL.port_b.p, has value: " + String(pipeL.port_b.p, "g"));
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_357(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,357};
  modelica_boolean tmp0;
  static const MMC_DEFSTRINGLIT(tmp1,69,"Variable violating min constraint: 0.0 <= pipeL.port_b.p, has value: ");
  modelica_string tmp2;
  modelica_metatype tmpMeta3;
  static int tmp4 = 0;
  if(!tmp4)
  {
    tmp0 = GreaterEq((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[59]] /* pipeL.port_b.p variable */),0.0);
    if(!tmp0)
    {
      tmp2 = modelica_real_to_modelica_string_format((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[59]] /* pipeL.port_b.p variable */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta3 = stringAppend(MMC_REFSTRINGLIT(tmp1),tmp2);
      {
        const char* assert_cond = "(pipeL.port_b.p >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta3));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta3));
        }
      }
      tmp4 = 1;
    }
  }
  threadData->lastEquationSolved = 357;
}

/*
equation index: 358
type: ALGORITHM

  assert(pipeR.port_b.p >= 0.0, "Variable violating min constraint: 0.0 <= pipeR.port_b.p, has value: " + String(pipeR.port_b.p, "g"));
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_358(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,358};
  modelica_boolean tmp5;
  static const MMC_DEFSTRINGLIT(tmp6,69,"Variable violating min constraint: 0.0 <= pipeR.port_b.p, has value: ");
  modelica_string tmp7;
  modelica_metatype tmpMeta8;
  static int tmp9 = 0;
  if(!tmp9)
  {
    tmp5 = GreaterEq((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[65]] /* pipeR.port_b.p variable */),0.0);
    if(!tmp5)
    {
      tmp7 = modelica_real_to_modelica_string_format((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[65]] /* pipeR.port_b.p variable */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta8 = stringAppend(MMC_REFSTRINGLIT(tmp6),tmp7);
      {
        const char* assert_cond = "(pipeR.port_b.p >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta8));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta8));
        }
      }
      tmp9 = 1;
    }
  }
  threadData->lastEquationSolved = 358;
}

/*
equation index: 359
type: ALGORITHM

  assert(reliefRL.port_a.p >= 0.0, "Variable violating min constraint: 0.0 <= reliefRL.port_a.p, has value: " + String(reliefRL.port_a.p, "g"));
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_359(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,359};
  modelica_boolean tmp10;
  static const MMC_DEFSTRINGLIT(tmp11,72,"Variable violating min constraint: 0.0 <= reliefRL.port_a.p, has value: ");
  modelica_string tmp12;
  modelica_metatype tmpMeta13;
  static int tmp14 = 0;
  if(!tmp14)
  {
    tmp10 = GreaterEq((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */),0.0);
    if(!tmp10)
    {
      tmp12 = modelica_real_to_modelica_string_format((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[82]] /* reliefRL.port_a.p variable */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta13 = stringAppend(MMC_REFSTRINGLIT(tmp11),tmp12);
      {
        const char* assert_cond = "(reliefRL.port_a.p >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta13));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta13));
        }
      }
      tmp14 = 1;
    }
  }
  threadData->lastEquationSolved = 359;
}

/*
equation index: 360
type: ALGORITHM

  assert(reliefRL.port_b.p >= 0.0, "Variable violating min constraint: 0.0 <= reliefRL.port_b.p, has value: " + String(reliefRL.port_b.p, "g"));
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_360(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,360};
  modelica_boolean tmp15;
  static const MMC_DEFSTRINGLIT(tmp16,72,"Variable violating min constraint: 0.0 <= reliefRL.port_b.p, has value: ");
  modelica_string tmp17;
  modelica_metatype tmpMeta18;
  static int tmp19 = 0;
  if(!tmp19)
  {
    tmp15 = GreaterEq((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */),0.0);
    if(!tmp15)
    {
      tmp17 = modelica_real_to_modelica_string_format((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[83]] /* reliefRL.port_b.p variable */), (modelica_string) mmc_strings_len1[103]);
      tmpMeta18 = stringAppend(MMC_REFSTRINGLIT(tmp16),tmp17);
      {
        const char* assert_cond = "(reliefRL.port_b.p >= 0.0)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta18));
        } else {
          FILE_INFO info = {"/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Interfaces/HydraulicPort.mo",3,3,3,75,0};
          omc_assert_warning_withEquationIndexes(info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(tmpMeta18));
        }
      }
      tmp19 = 1;
    }
  }
  threadData->lastEquationSolved = 360;
}
/* function to check assert after a step is done */
OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_checkForAsserts(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[4])(DATA*, threadData_t*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_357,
    FishRobot_Examples_HydraulicsStep_eqFunction_358,
    FishRobot_Examples_HydraulicsStep_eqFunction_359,
    FishRobot_Examples_HydraulicsStep_eqFunction_360
  };
  
  for (int id = 0; id < 4; id++) {
    eqFunctions[id](data, threadData);
  }
  
  return 0;
}

#if defined(__cplusplus)
}
#endif
