/* Jacobians 9 */
#include "FishRobot.Examples.HydraulicsStep_model.h"
#include "FishRobot.Examples.HydraulicsStep_12jac.h"
#include "simulation/jacobian_util.h"
#include "util/omc_file.h"
/* constant equations */
/* dynamic equations */

/*
equation index: 54
type: SIMPLE_ASSIGN
pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 = (pipeR.R_lam + pipeR.R_turb * sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)) * pipeR.V_flow.SeedNLSJac0 + pipeR.R_turb * pipeR.V_flow ^ 2.0 * pipeR.V_flow.SeedNLSJac0 / sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_54(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 0;
  const int equationIndexes[2] = {1,54};
  modelica_real tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  modelica_real tmp3;
  modelica_real tmp4;
  modelica_real tmp5;
  modelica_real tmp6;
  tmp0 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp1 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[157]] /* pipeR.V_flow_small PARAM */);
  tmp2 = (tmp0 * tmp0) + (tmp1 * tmp1);
  if(!(tmp2 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0) was %g should be >= 0", tmp2);
    }
  }tmp3 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp4 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp5 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[157]] /* pipeR.V_flow_small PARAM */);
  tmp6 = (tmp4 * tmp4) + (tmp5 * tmp5);
  if(!(tmp6 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0) was %g should be >= 0", tmp6);
    }
  }
  jacobian->tmpVars[4] /* pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[155]] /* pipeR.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[156]] /* pipeR.R_turb PARAM */)) * (sqrt(tmp2))) * (jacobian->seedVars[0] /* pipeR.V_flow.SeedNLSJac0 SEED_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[156]] /* pipeR.R_turb PARAM */)) * (((tmp3 * tmp3)) * (DIVISION(jacobian->seedVars[0] /* pipeR.V_flow.SeedNLSJac0 SEED_VAR */,sqrt(tmp6),"sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)")));
  threadData->lastEquationSolved = 54;
}

/*
equation index: 55
type: SIMPLE_ASSIGN
reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0 = pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 + reliefLR.dp.SeedNLSJac0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_55(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 1;
  const int equationIndexes[2] = {1,55};
  jacobian->tmpVars[9] /* reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[4] /* pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ + jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac0 SEED_VAR */;
  threadData->lastEquationSolved = 55;
}

/*
equation index: 56
type: SIMPLE_ASSIGN
pump.dp_pump.$pDERNLSJac0.dummyVarNLSJac0 = pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 + reliefLR.dp.SeedNLSJac0 - reliefRL.dp.SeedNLSJac0 - reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_56(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 2;
  const int equationIndexes[2] = {1,56};
  jacobian->tmpVars[10] /* pump.dp_pump.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[4] /* pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ + jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac0 SEED_VAR */ - jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac0 SEED_VAR */ - jacobian->tmpVars[9] /* reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 56;
}

/*
equation index: 57
type: SIMPLE_ASSIGN
$res_NLSJac0_3.$pDERNLSJac0.dummyVarNLSJac0 = pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 + pump.dp_pump.$pDERNLSJac0.dummyVarNLSJac0 - reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_57(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 3;
  const int equationIndexes[2] = {1,57};
  jacobian->resultVars[2] /* $res_NLSJac0_3.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_VAR */ = jacobian->tmpVars[4] /* pipeR.dp.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ + jacobian->tmpVars[10] /* pump.dp_pump.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ - jacobian->tmpVars[9] /* reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 57;
}

/*
equation index: 58
type: SIMPLE_ASSIGN
reliefRL.dp_over.$pDERNLSJac0.dummyVarNLSJac0 = 0.5 * (reliefRL.dp.SeedNLSJac0 + (reliefRL.dp - reliefRL.p_set) * reliefRL.dp.SeedNLSJac0 / sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_58(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 4;
  const int equationIndexes[2] = {1,58};
  modelica_real tmp7;
  modelica_real tmp8;
  modelica_real tmp9;
  tmp7 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */);
  tmp8 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[179]] /* reliefRL.dp_smooth PARAM */);
  tmp9 = (tmp7 * tmp7) + (tmp8 * tmp8);
  if(!(tmp9 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0) was %g should be >= 0", tmp9);
    }
  }
  jacobian->tmpVars[2] /* reliefRL.dp_over.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = (0.5) * (jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac0 SEED_VAR */ + ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */)) * (DIVISION(jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac0 SEED_VAR */,sqrt(tmp9),"sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0)")));
  threadData->lastEquationSolved = 58;
}

/*
equation index: 59
type: SIMPLE_ASSIGN
reliefRL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 = reliefRL.G_leak * reliefRL.dp.SeedNLSJac0 + reliefRL.G_open * reliefRL.dp_over.$pDERNLSJac0.dummyVarNLSJac0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_59(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 5;
  const int equationIndexes[2] = {1,59};
  jacobian->tmpVars[3] /* reliefRL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[175]] /* reliefRL.G_leak PARAM */)) * (jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac0 SEED_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[176]] /* reliefRL.G_open PARAM */)) * (jacobian->tmpVars[2] /* reliefRL.dp_over.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */);
  threadData->lastEquationSolved = 59;
}

/*
equation index: 60
type: SIMPLE_ASSIGN
reliefLR.dp_over.$pDERNLSJac0.dummyVarNLSJac0 = 0.5 * (reliefLR.dp.SeedNLSJac0 + (reliefLR.dp - reliefLR.p_set) * reliefLR.dp.SeedNLSJac0 / sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_60(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 6;
  const int equationIndexes[2] = {1,60};
  modelica_real tmp10;
  modelica_real tmp11;
  modelica_real tmp12;
  tmp10 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */);
  tmp11 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[173]] /* reliefLR.dp_smooth PARAM */);
  tmp12 = (tmp10 * tmp10) + (tmp11 * tmp11);
  if(!(tmp12 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0) was %g should be >= 0", tmp12);
    }
  }
  jacobian->tmpVars[0] /* reliefLR.dp_over.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = (0.5) * (jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac0 SEED_VAR */ + ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */)) * (DIVISION(jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac0 SEED_VAR */,sqrt(tmp12),"sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0)")));
  threadData->lastEquationSolved = 60;
}

/*
equation index: 61
type: SIMPLE_ASSIGN
reliefLR.V_flow.$pDERNLSJac0.dummyVarNLSJac0 = reliefLR.G_leak * reliefLR.dp.SeedNLSJac0 + reliefLR.G_open * reliefLR.dp_over.$pDERNLSJac0.dummyVarNLSJac0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_61(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 7;
  const int equationIndexes[2] = {1,61};
  jacobian->tmpVars[1] /* reliefLR.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[169]] /* reliefLR.G_leak PARAM */)) * (jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac0 SEED_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[170]] /* reliefLR.G_open PARAM */)) * (jacobian->tmpVars[0] /* reliefLR.dp_over.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */);
  threadData->lastEquationSolved = 61;
}

/*
equation index: 62
type: SIMPLE_ASSIGN
Q_pump.$pDERNLSJac0.dummyVarNLSJac0 = reliefLR.V_flow.$pDERNLSJac0.dummyVarNLSJac0 - (reliefRL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 + pipeR.V_flow.SeedNLSJac0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_62(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 8;
  const int equationIndexes[2] = {1,62};
  jacobian->tmpVars[5] /* Q_pump.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[1] /* reliefLR.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ - (jacobian->tmpVars[3] /* reliefRL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ + jacobian->seedVars[0] /* pipeR.V_flow.SeedNLSJac0 SEED_VAR */);
  threadData->lastEquationSolved = 62;
}

/*
equation index: 63
type: SIMPLE_ASSIGN
$res_NLSJac0_2.$pDERNLSJac0.dummyVarNLSJac0 = (-pump.k_leak) * pump.dp_pump.$pDERNLSJac0.dummyVarNLSJac0 - Q_pump.$pDERNLSJac0.dummyVarNLSJac0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_63(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 9;
  const int equationIndexes[2] = {1,63};
  jacobian->resultVars[1] /* $res_NLSJac0_2.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_VAR */ = ((-(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[167]] /* pump.k_leak PARAM */))) * (jacobian->tmpVars[10] /* pump.dp_pump.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */) - jacobian->tmpVars[5] /* Q_pump.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 63;
}

/*
equation index: 64
type: SIMPLE_ASSIGN
pipeL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 = reliefRL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 - (reliefLR.V_flow.$pDERNLSJac0.dummyVarNLSJac0 - Q_pump.$pDERNLSJac0.dummyVarNLSJac0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_64(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 10;
  const int equationIndexes[2] = {1,64};
  jacobian->tmpVars[6] /* pipeL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[3] /* reliefRL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ - (jacobian->tmpVars[1] /* reliefLR.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ - jacobian->tmpVars[5] /* Q_pump.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */);
  threadData->lastEquationSolved = 64;
}

/*
equation index: 65
type: SIMPLE_ASSIGN
pipeL.dp.$pDERNLSJac0.dummyVarNLSJac0 = (pipeL.R_lam + pipeL.R_turb * sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)) * pipeL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 + pipeL.R_turb * pipeL.V_flow ^ 2.0 * pipeL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 / sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_65(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 11;
  const int equationIndexes[2] = {1,65};
  modelica_real tmp13;
  modelica_real tmp14;
  modelica_real tmp15;
  modelica_real tmp16;
  modelica_real tmp17;
  modelica_real tmp18;
  modelica_real tmp19;
  tmp13 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp14 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[146]] /* pipeL.V_flow_small PARAM */);
  tmp15 = (tmp13 * tmp13) + (tmp14 * tmp14);
  if(!(tmp15 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0) was %g should be >= 0", tmp15);
    }
  }tmp16 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp17 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp18 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[146]] /* pipeL.V_flow_small PARAM */);
  tmp19 = (tmp17 * tmp17) + (tmp18 * tmp18);
  if(!(tmp19 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0) was %g should be >= 0", tmp19);
    }
  }
  jacobian->tmpVars[7] /* pipeL.dp.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[144]] /* pipeL.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[145]] /* pipeL.R_turb PARAM */)) * (sqrt(tmp15))) * (jacobian->tmpVars[6] /* pipeL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[145]] /* pipeL.R_turb PARAM */)) * (((tmp16 * tmp16)) * (DIVISION(jacobian->tmpVars[6] /* pipeL.V_flow.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */,sqrt(tmp19),"sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)")));
  threadData->lastEquationSolved = 65;
}

/*
equation index: 66
type: SIMPLE_ASSIGN
$res_NLSJac0_1.$pDERNLSJac0.dummyVarNLSJac0 = reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0 - pipeL.dp.$pDERNLSJac0.dummyVarNLSJac0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_66(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 12;
  const int equationIndexes[2] = {1,66};
  jacobian->resultVars[0] /* $res_NLSJac0_1.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_VAR */ = jacobian->tmpVars[9] /* reliefRL.port_b.p.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */ - jacobian->tmpVars[7] /* pipeL.dp.$pDERNLSJac0.dummyVarNLSJac0 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 66;
}

OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_functionJacNLSJac0_constantEqns(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = FishRobot_Examples_HydraulicsStep_INDEX_JAC_NLSJac0;
  
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_functionJacNLSJac0_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = FishRobot_Examples_HydraulicsStep_INDEX_JAC_NLSJac0;
  
  static void (*const eqFunctions[13])(DATA*, threadData_t*, JACOBIAN*, JACOBIAN*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_54,
    FishRobot_Examples_HydraulicsStep_eqFunction_55,
    FishRobot_Examples_HydraulicsStep_eqFunction_56,
    FishRobot_Examples_HydraulicsStep_eqFunction_57,
    FishRobot_Examples_HydraulicsStep_eqFunction_58,
    FishRobot_Examples_HydraulicsStep_eqFunction_59,
    FishRobot_Examples_HydraulicsStep_eqFunction_60,
    FishRobot_Examples_HydraulicsStep_eqFunction_61,
    FishRobot_Examples_HydraulicsStep_eqFunction_62,
    FishRobot_Examples_HydraulicsStep_eqFunction_63,
    FishRobot_Examples_HydraulicsStep_eqFunction_64,
    FishRobot_Examples_HydraulicsStep_eqFunction_65,
    FishRobot_Examples_HydraulicsStep_eqFunction_66
  };
  
  if (jacobian->evalSelection) {
    for (int i = 0; i < jacobian->evalSelection->n; i++) {
      int id = jacobian->evalSelection->idx[i];
      eqFunctions[id](data, threadData, jacobian, parentJacobian);
    }
  } else {
    for (int id = 0; id < 13; id++) {
      eqFunctions[id](data, threadData, jacobian, parentJacobian);
    }
  }
  
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacNLSJac0_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian)
{
  const size_t eqMap[] = {54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66};
  buildEvalDAG_Jac(jacobian, data->modelData, sizeof(eqMap)/sizeof(size_t), eqMap);
}

/* constant equations */
/* dynamic equations */

/*
equation index: 156
type: SIMPLE_ASSIGN
pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1 = (pipeL.R_lam + pipeL.R_turb * sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)) * pipeL.V_flow.SeedNLSJac1 + pipeL.R_turb * pipeL.V_flow ^ 2.0 * pipeL.V_flow.SeedNLSJac1 / sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_156(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 0;
  const int equationIndexes[2] = {1,156};
  modelica_real tmp20;
  modelica_real tmp21;
  modelica_real tmp22;
  modelica_real tmp23;
  modelica_real tmp24;
  modelica_real tmp25;
  modelica_real tmp26;
  tmp20 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp21 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[146]] /* pipeL.V_flow_small PARAM */);
  tmp22 = (tmp20 * tmp20) + (tmp21 * tmp21);
  if(!(tmp22 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0) was %g should be >= 0", tmp22);
    }
  }tmp23 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp24 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  tmp25 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[146]] /* pipeL.V_flow_small PARAM */);
  tmp26 = (tmp24 * tmp24) + (tmp25 * tmp25);
  if(!(tmp26 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0) was %g should be >= 0", tmp26);
    }
  }
  jacobian->tmpVars[4] /* pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[144]] /* pipeL.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[145]] /* pipeL.R_turb PARAM */)) * (sqrt(tmp22))) * (jacobian->seedVars[0] /* pipeL.V_flow.SeedNLSJac1 SEED_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[145]] /* pipeL.R_turb PARAM */)) * (((tmp23 * tmp23)) * (DIVISION(jacobian->seedVars[0] /* pipeL.V_flow.SeedNLSJac1 SEED_VAR */,sqrt(tmp26),"sqrt(pipeL.V_flow ^ 2.0 + pipeL.V_flow_small ^ 2.0)")));
  threadData->lastEquationSolved = 156;
}

/*
equation index: 157
type: SIMPLE_ASSIGN
reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 = pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1 - reliefLR.dp.SeedNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_157(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 1;
  const int equationIndexes[2] = {1,157};
  jacobian->tmpVars[9] /* reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[4] /* pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ - jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac1 SEED_VAR */;
  threadData->lastEquationSolved = 157;
}

/*
equation index: 158
type: SIMPLE_ASSIGN
pump.dp_pump.$pDERNLSJac1.dummyVarNLSJac1 = reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 + reliefLR.dp.SeedNLSJac1 - reliefRL.dp.SeedNLSJac1 - pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_158(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 2;
  const int equationIndexes[2] = {1,158};
  jacobian->tmpVars[10] /* pump.dp_pump.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[9] /* reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ + jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac1 SEED_VAR */ - jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac1 SEED_VAR */ - jacobian->tmpVars[4] /* pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 158;
}

/*
equation index: 159
type: SIMPLE_ASSIGN
$res_NLSJac1_2.$pDERNLSJac1.dummyVarNLSJac1 = reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 + pump.dp_pump.$pDERNLSJac1.dummyVarNLSJac1 - pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_159(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 3;
  const int equationIndexes[2] = {1,159};
  jacobian->resultVars[1] /* $res_NLSJac1_2.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_VAR */ = jacobian->tmpVars[9] /* reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ + jacobian->tmpVars[10] /* pump.dp_pump.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ - jacobian->tmpVars[4] /* pipeL.dp.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 159;
}

/*
equation index: 160
type: SIMPLE_ASSIGN
reliefRL.dp_over.$pDERNLSJac1.dummyVarNLSJac1 = 0.5 * (reliefRL.dp.SeedNLSJac1 + (reliefRL.dp - reliefRL.p_set) * reliefRL.dp.SeedNLSJac1 / sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_160(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 4;
  const int equationIndexes[2] = {1,160};
  modelica_real tmp27;
  modelica_real tmp28;
  modelica_real tmp29;
  tmp27 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */);
  tmp28 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[179]] /* reliefRL.dp_smooth PARAM */);
  tmp29 = (tmp27 * tmp27) + (tmp28 * tmp28);
  if(!(tmp29 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0) was %g should be >= 0", tmp29);
    }
  }
  jacobian->tmpVars[2] /* reliefRL.dp_over.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = (0.5) * (jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac1 SEED_VAR */ + ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[180]] /* reliefRL.p_set PARAM */)) * (DIVISION(jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac1 SEED_VAR */,sqrt(tmp29),"sqrt((reliefRL.dp - reliefRL.p_set) ^ 2.0 + reliefRL.dp_smooth ^ 2.0)")));
  threadData->lastEquationSolved = 160;
}

/*
equation index: 161
type: SIMPLE_ASSIGN
reliefRL.V_flow.$pDERNLSJac1.dummyVarNLSJac1 = reliefRL.G_leak * reliefRL.dp.SeedNLSJac1 + reliefRL.G_open * reliefRL.dp_over.$pDERNLSJac1.dummyVarNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_161(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 5;
  const int equationIndexes[2] = {1,161};
  jacobian->tmpVars[3] /* reliefRL.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[175]] /* reliefRL.G_leak PARAM */)) * (jacobian->seedVars[1] /* reliefRL.dp.SeedNLSJac1 SEED_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[176]] /* reliefRL.G_open PARAM */)) * (jacobian->tmpVars[2] /* reliefRL.dp_over.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */);
  threadData->lastEquationSolved = 161;
}

/*
equation index: 162
type: SIMPLE_ASSIGN
reliefLR.dp_over.$pDERNLSJac1.dummyVarNLSJac1 = 0.5 * (reliefLR.dp.SeedNLSJac1 + (reliefLR.dp - reliefLR.p_set) * reliefLR.dp.SeedNLSJac1 / sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_162(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 6;
  const int equationIndexes[2] = {1,162};
  modelica_real tmp30;
  modelica_real tmp31;
  modelica_real tmp32;
  tmp30 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */);
  tmp31 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[173]] /* reliefLR.dp_smooth PARAM */);
  tmp32 = (tmp30 * tmp30) + (tmp31 * tmp31);
  if(!(tmp32 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0) was %g should be >= 0", tmp32);
    }
  }
  jacobian->tmpVars[0] /* reliefLR.dp_over.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = (0.5) * (jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac1 SEED_VAR */ + ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[174]] /* reliefLR.p_set PARAM */)) * (DIVISION(jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac1 SEED_VAR */,sqrt(tmp32),"sqrt((reliefLR.dp - reliefLR.p_set) ^ 2.0 + reliefLR.dp_smooth ^ 2.0)")));
  threadData->lastEquationSolved = 162;
}

/*
equation index: 163
type: SIMPLE_ASSIGN
reliefLR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 = reliefLR.G_leak * reliefLR.dp.SeedNLSJac1 + reliefLR.G_open * reliefLR.dp_over.$pDERNLSJac1.dummyVarNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_163(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 7;
  const int equationIndexes[2] = {1,163};
  jacobian->tmpVars[1] /* reliefLR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[169]] /* reliefLR.G_leak PARAM */)) * (jacobian->seedVars[2] /* reliefLR.dp.SeedNLSJac1 SEED_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[170]] /* reliefLR.G_open PARAM */)) * (jacobian->tmpVars[0] /* reliefLR.dp_over.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */);
  threadData->lastEquationSolved = 163;
}

/*
equation index: 164
type: SIMPLE_ASSIGN
Q_pump.$pDERNLSJac1.dummyVarNLSJac1 = reliefLR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 + pipeL.V_flow.SeedNLSJac1 - reliefRL.V_flow.$pDERNLSJac1.dummyVarNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_164(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 8;
  const int equationIndexes[2] = {1,164};
  jacobian->tmpVars[5] /* Q_pump.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[1] /* reliefLR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ + jacobian->seedVars[0] /* pipeL.V_flow.SeedNLSJac1 SEED_VAR */ - jacobian->tmpVars[3] /* reliefRL.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 164;
}

/*
equation index: 165
type: SIMPLE_ASSIGN
$res_NLSJac1_3.$pDERNLSJac1.dummyVarNLSJac1 = (-Q_pump.$pDERNLSJac1.dummyVarNLSJac1) - pump.k_leak * pump.dp_pump.$pDERNLSJac1.dummyVarNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_165(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 9;
  const int equationIndexes[2] = {1,165};
  jacobian->resultVars[2] /* $res_NLSJac1_3.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_VAR */ = (-jacobian->tmpVars[5] /* Q_pump.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */) - (((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[167]] /* pump.k_leak PARAM */)) * (jacobian->tmpVars[10] /* pump.dp_pump.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */));
  threadData->lastEquationSolved = 165;
}

/*
equation index: 166
type: SIMPLE_ASSIGN
pipeR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 = reliefLR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 - (reliefRL.V_flow.$pDERNLSJac1.dummyVarNLSJac1 + Q_pump.$pDERNLSJac1.dummyVarNLSJac1)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_166(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 10;
  const int equationIndexes[2] = {1,166};
  jacobian->tmpVars[6] /* pipeR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = jacobian->tmpVars[1] /* reliefLR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ - (jacobian->tmpVars[3] /* reliefRL.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ + jacobian->tmpVars[5] /* Q_pump.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */);
  threadData->lastEquationSolved = 166;
}

/*
equation index: 167
type: SIMPLE_ASSIGN
pipeR.dp.$pDERNLSJac1.dummyVarNLSJac1 = (pipeR.R_lam + pipeR.R_turb * sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)) * pipeR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 + pipeR.R_turb * pipeR.V_flow ^ 2.0 * pipeR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 / sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_167(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 11;
  const int equationIndexes[2] = {1,167};
  modelica_real tmp33;
  modelica_real tmp34;
  modelica_real tmp35;
  modelica_real tmp36;
  modelica_real tmp37;
  modelica_real tmp38;
  modelica_real tmp39;
  tmp33 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp34 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[157]] /* pipeR.V_flow_small PARAM */);
  tmp35 = (tmp33 * tmp33) + (tmp34 * tmp34);
  if(!(tmp35 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0) was %g should be >= 0", tmp35);
    }
  }tmp36 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp37 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  tmp38 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[157]] /* pipeR.V_flow_small PARAM */);
  tmp39 = (tmp37 * tmp37) + (tmp38 * tmp38);
  if(!(tmp39 >= 0.0))
  {
    if (data->simulationInfo->noThrowAsserts) {
      FILE_INFO info = {"",0,0,0,0,0};
      infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      data->simulationInfo->needToReThrow = 1;
    } else {
      FILE_INFO info = {"",0,0,0,0,0};
      omc_assert_warning(info, "The following assertion has been violated %sat time %f", initial() ? "during initialization " : "", data->localData[0]->timeValue);
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0) was %g should be >= 0", tmp39);
    }
  }
  jacobian->tmpVars[7] /* pipeR.dp.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[155]] /* pipeR.R_lam PARAM */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[156]] /* pipeR.R_turb PARAM */)) * (sqrt(tmp35))) * (jacobian->tmpVars[6] /* pipeR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */) + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[156]] /* pipeR.R_turb PARAM */)) * (((tmp36 * tmp36)) * (DIVISION(jacobian->tmpVars[6] /* pipeR.V_flow.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */,sqrt(tmp39),"sqrt(pipeR.V_flow ^ 2.0 + pipeR.V_flow_small ^ 2.0)")));
  threadData->lastEquationSolved = 167;
}

/*
equation index: 168
type: SIMPLE_ASSIGN
$res_NLSJac1_1.$pDERNLSJac1.dummyVarNLSJac1 = reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 - pipeR.dp.$pDERNLSJac1.dummyVarNLSJac1
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_168(DATA *data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  const int baseClockIndex = 0;
  const int subClockIndex = 12;
  const int equationIndexes[2] = {1,168};
  jacobian->resultVars[0] /* $res_NLSJac1_1.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_VAR */ = jacobian->tmpVars[9] /* reliefRL.port_a.p.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */ - jacobian->tmpVars[7] /* pipeR.dp.$pDERNLSJac1.dummyVarNLSJac1 JACOBIAN_TMP_VAR */;
  threadData->lastEquationSolved = 168;
}

OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_functionJacNLSJac1_constantEqns(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = FishRobot_Examples_HydraulicsStep_INDEX_JAC_NLSJac1;
  
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_functionJacNLSJac1_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = FishRobot_Examples_HydraulicsStep_INDEX_JAC_NLSJac1;
  
  static void (*const eqFunctions[13])(DATA*, threadData_t*, JACOBIAN*, JACOBIAN*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_156,
    FishRobot_Examples_HydraulicsStep_eqFunction_157,
    FishRobot_Examples_HydraulicsStep_eqFunction_158,
    FishRobot_Examples_HydraulicsStep_eqFunction_159,
    FishRobot_Examples_HydraulicsStep_eqFunction_160,
    FishRobot_Examples_HydraulicsStep_eqFunction_161,
    FishRobot_Examples_HydraulicsStep_eqFunction_162,
    FishRobot_Examples_HydraulicsStep_eqFunction_163,
    FishRobot_Examples_HydraulicsStep_eqFunction_164,
    FishRobot_Examples_HydraulicsStep_eqFunction_165,
    FishRobot_Examples_HydraulicsStep_eqFunction_166,
    FishRobot_Examples_HydraulicsStep_eqFunction_167,
    FishRobot_Examples_HydraulicsStep_eqFunction_168
  };
  
  if (jacobian->evalSelection) {
    for (int i = 0; i < jacobian->evalSelection->n; i++) {
      int id = jacobian->evalSelection->idx[i];
      eqFunctions[id](data, threadData, jacobian, parentJacobian);
    }
  } else {
    for (int id = 0; id < 13; id++) {
      eqFunctions[id](data, threadData, jacobian, parentJacobian);
    }
  }
  
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacNLSJac1_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian)
{
  const size_t eqMap[] = {156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168};
  buildEvalDAG_Jac(jacobian, data->modelData, sizeof(eqMap)/sizeof(size_t), eqMap);
}

int FishRobot_Examples_HydraulicsStep_functionJacADJ_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacADJ_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian) { /* empty */ }

int FishRobot_Examples_HydraulicsStep_functionJacH_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacH_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian) { /* empty */ }

int FishRobot_Examples_HydraulicsStep_functionJacF_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacF_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian) { /* empty */ }

int FishRobot_Examples_HydraulicsStep_functionJacD_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacD_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian) { /* empty */ }

int FishRobot_Examples_HydraulicsStep_functionJacC_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacC_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian) { /* empty */ }

int FishRobot_Examples_HydraulicsStep_functionJacB_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacB_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian) { /* empty */ }

/* constant equations */
/* dynamic equations */

OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_functionJacA_constantEqns(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = FishRobot_Examples_HydraulicsStep_INDEX_JAC_A;
  
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_functionJacA_column(DATA* data, threadData_t *threadData, JACOBIAN *jacobian, JACOBIAN *parentJacobian)
{
  int index = FishRobot_Examples_HydraulicsStep_INDEX_JAC_A;
  
  
  return 0;
}

void FishRobot_Examples_HydraulicsStep_JacA_DAG(DATA* data, threadData_t* threadData, JACOBIAN* jacobian)
{
  const size_t eqMap[] = {};
  buildEvalDAG_Jac(jacobian, data->modelData, sizeof(eqMap)/sizeof(size_t), eqMap);
}

OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianNLSJac0(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  size_t count;

  FILE* pFile = openSparsePatternFile(data, threadData, "FishRobot.Examples.HydraulicsStep_JacNLSJac0.bin");
  
  initJacobian(jacobian, 3, 3, 14, NULL, FishRobot_Examples_HydraulicsStep_functionJacNLSJac0_column, NULL, NULL);
  jacobian->sparsePattern = allocSparsePattern(3, 9, 3);
  jacobian->availability = JACOBIAN_AVAILABLE;
  jacobian->isRowEval = 0 /* false */;
  
  /* read lead index of compressed sparse column */
  count = omc_fread(jacobian->sparsePattern->leadindex, sizeof(unsigned int), 3+1, pFile, FALSE);
  if (count != 3+1) {
    throwStreamPrint(threadData, "Error while reading lead index list of sparsity pattern. Expected %d, got %zu", 3+1, count);
  }
  
  /* read sparse index */
  count = omc_fread(jacobian->sparsePattern->index, sizeof(unsigned int), 9, pFile, FALSE);
  if (count != 9) {
    throwStreamPrint(threadData, "Error while reading row index list of sparsity pattern. Expected %d, got %zu", 9, count);
  }
  
  /* write color array */
  /* color 1 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 1, 1, 3);
  /* color 2 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 2, 1, 3);
  /* color 3 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 3, 1, 3);
  
  omc_fclose(pFile);
  
  return 0;
}
OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianNLSJac1(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  size_t count;

  FILE* pFile = openSparsePatternFile(data, threadData, "FishRobot.Examples.HydraulicsStep_JacNLSJac1.bin");
  
  initJacobian(jacobian, 3, 3, 14, NULL, FishRobot_Examples_HydraulicsStep_functionJacNLSJac1_column, NULL, NULL);
  jacobian->sparsePattern = allocSparsePattern(3, 9, 3);
  jacobian->availability = JACOBIAN_AVAILABLE;
  jacobian->isRowEval = 0 /* false */;
  
  /* read lead index of compressed sparse column */
  count = omc_fread(jacobian->sparsePattern->leadindex, sizeof(unsigned int), 3+1, pFile, FALSE);
  if (count != 3+1) {
    throwStreamPrint(threadData, "Error while reading lead index list of sparsity pattern. Expected %d, got %zu", 3+1, count);
  }
  
  /* read sparse index */
  count = omc_fread(jacobian->sparsePattern->index, sizeof(unsigned int), 9, pFile, FALSE);
  if (count != 9) {
    throwStreamPrint(threadData, "Error while reading row index list of sparsity pattern. Expected %d, got %zu", 9, count);
  }
  
  /* write color array */
  /* color 1 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 1, 1, 3);
  /* color 2 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 2, 1, 3);
  /* color 3 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 3, 1, 3);
  
  omc_fclose(pFile);
  
  return 0;
}
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianADJ(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianH(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianF(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianD(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianC(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianB(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  jacobian->availability = JACOBIAN_NOT_AVAILABLE;
  return 1;
}
OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianA(DATA* data, threadData_t *threadData, JACOBIAN *jacobian)
{
  size_t count;

  FILE* pFile = openSparsePatternFile(data, threadData, "FishRobot.Examples.HydraulicsStep_JacA.bin");
  
  initJacobian(jacobian, 8, 8, 0, NULL, FishRobot_Examples_HydraulicsStep_functionJacA_column, NULL, NULL);
  jacobian->sparsePattern = allocSparsePattern(8, 20, 4);
  jacobian->availability = JACOBIAN_ONLY_SPARSITY;
  jacobian->isRowEval = 0 /* false */;
  
  /* read lead index of compressed sparse column */
  count = omc_fread(jacobian->sparsePattern->leadindex, sizeof(unsigned int), 8+1, pFile, FALSE);
  if (count != 8+1) {
    throwStreamPrint(threadData, "Error while reading lead index list of sparsity pattern. Expected %d, got %zu", 8+1, count);
  }
  
  /* read sparse index */
  count = omc_fread(jacobian->sparsePattern->index, sizeof(unsigned int), 20, pFile, FALSE);
  if (count != 20) {
    throwStreamPrint(threadData, "Error while reading row index list of sparsity pattern. Expected %d, got %zu", 20, count);
  }
  
  /* write color array */
  /* color 1 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 1, 1, 8);
  /* color 2 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 2, 1, 8);
  /* color 3 with 1 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 3, 1, 8);
  /* color 4 with 5 columns */
  readSparsePatternColor(threadData, pFile, jacobian->sparsePattern->colorCols, 4, 5, 8);
  
  omc_fclose(pFile);
  
  return 0;
}


