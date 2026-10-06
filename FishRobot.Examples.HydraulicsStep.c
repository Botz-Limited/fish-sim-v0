/* Main Simulation File */

#if defined(__cplusplus)
extern "C" {
#endif

#include "FishRobot.Examples.HydraulicsStep_model.h"
#include "simulation/solver/events.h"
#include "simulation/arrayIndex.h"

/* FIXME these defines are ugly and hard to read, why not use direct function pointers instead? */
#define prefixedName_performSimulation FishRobot_Examples_HydraulicsStep_performSimulation
#define prefixedName_updateContinuousSystem FishRobot_Examples_HydraulicsStep_updateContinuousSystem
#include <simulation/solver/perform_simulation.c.inc>

#define prefixedName_performQSSSimulation FishRobot_Examples_HydraulicsStep_performQSSSimulation
#include <simulation/solver/perform_qss_simulation.c.inc>


/* dummy VARINFO and FILEINFO */
const VAR_INFO dummyVAR_INFO = omc_dummyVarInfo;

int FishRobot_Examples_HydraulicsStep_input_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_input_function_init(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_input_function_updateStartValues(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_inputNames(DATA *data, char ** names){
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_data_function(DATA *data, threadData_t *threadData)
{
  return 0;
}

int FishRobot_Examples_HydraulicsStep_dataReconciliationInputNames(DATA *data, char ** names){
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_dataReconciliationUnmeasuredVariables(DATA *data, char ** names)
{
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_output_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_setc_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

int FishRobot_Examples_HydraulicsStep_setb_function(DATA *data, threadData_t *threadData)
{
  
  return 0;
}


/*
equation index: 104
type: SIMPLE_ASSIGN
ground.p.i = 0.0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_104(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,104};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[33]] /* ground.p.i variable */) = 0.0;
  threadData->lastEquationSolved = 104;
}

/*
equation index: 105
type: SIMPLE_ASSIGN
$DER.motor.emf.phi = -motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_105(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,105};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[16]] /* der(motor.emf.phi) DUMMY_DER */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 105;
}

/*
equation index: 106
type: SIMPLE_ASSIGN
motor.emf.w = -motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_106(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,106};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[42]] /* motor.emf.w variable */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 106;
}

/*
equation index: 107
type: SIMPLE_ASSIGN
$DER.motor.rotor.phi = -motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_107(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,107};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[17]] /* der(motor.rotor.phi) DUMMY_DER */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 107;
}

/*
equation index: 108
type: SIMPLE_ASSIGN
motor.rotor.w = -motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_108(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,108};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[52]] /* motor.rotor.w DUMMY_STATE */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 108;
}

/*
equation index: 109
type: SIMPLE_ASSIGN
motor.resistor.v = motor.resistor.R_actual * motor.inductor.i
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_109(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,109};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[48]] /* motor.resistor.v variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[46]] /* motor.resistor.R_actual variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* motor.inductor.i STATE(1) */));
  threadData->lastEquationSolved = 109;
}

/*
equation index: 110
type: SIMPLE_ASSIGN
motor.P_cu = motor.resistor.v * motor.inductor.i
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_110(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,110};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[36]] /* motor.P_cu variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[48]] /* motor.resistor.v variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* motor.inductor.i STATE(1) */));
  threadData->lastEquationSolved = 110;
}

/*
equation index: 111
type: SIMPLE_ASSIGN
motor.emf.v = (-motor.emf.k) * motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_111(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,111};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[41]] /* motor.emf.v variable */) = ((-(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[130]] /* motor.emf.k PARAM */))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 111;
}

/*
equation index: 112
type: SIMPLE_ASSIGN
motor.emf.tau = (-motor.emf.k) * motor.inductor.i
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_112(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,112};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[40]] /* motor.emf.tau variable */) = ((-(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[130]] /* motor.emf.k PARAM */))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* motor.inductor.i STATE(1) */));
  threadData->lastEquationSolved = 112;
}

/*
equation index: 113
type: SIMPLE_ASSIGN
motor.friction.tau = motor.friction.d * motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_113(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,113};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[44]] /* motor.friction.tau variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[131]] /* motor.friction.d PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 113;
}

/*
equation index: 114
type: SIMPLE_ASSIGN
motor.P_fric = motor.friction.tau * motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_114(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,114};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[38]] /* motor.P_fric variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[44]] /* motor.friction.tau variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 114;
}

/*
equation index: 115
type: SIMPLE_ASSIGN
$DER.motor.friction.phi_rel = motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_115(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,115};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[13]] /* der(motor.friction.phi_rel) STATE_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */);
  threadData->lastEquationSolved = 115;
}

/*
equation index: 116
type: SIMPLE_ASSIGN
command.timeScaled = time
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_116(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,116};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[31]] /* command.timeScaled variable */) = data->localData[0]->timeValue;
  threadData->lastEquationSolved = 116;
}

/*
equation index: 117
type: SIMPLE_ASSIGN
$whenCondition1 = time >= pre(command.nextTimeEvent)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_117(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,117};
  modelica_boolean tmp0;
  modelica_real tmp1;
  modelica_real tmp2;
  tmp1 = 1.0;
  tmp2 = 1.0;
  relationhysteresis(data, &tmp0, data->localData[0]->timeValue, (data->simulationInfo->realVarsPre[84] /* command.nextTimeEvent DISCRETE */), tmp1, tmp2, 0, GreaterEq, GreaterEqZC);
  (data->localData[0]->booleanVars[data->simulationInfo->booleanVarsIndex[0]] /* $whenCondition1 DISCRETE */) = tmp0;
  threadData->lastEquationSolved = 117;
}

/*
equation index: 118
type: WHEN

when {$whenCondition1} then
  command.nextTimeEventScaled = Modelica.Blocks.Tables.Internal.getNextTimeEvent(command.tableID, command.timeScaled);
end when;
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_118(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,118};
  if(((data->localData[0]->booleanVars[data->simulationInfo->booleanVarsIndex[0]] /* $whenCondition1 DISCRETE */) && !(data->simulationInfo->booleanVarsPre[0] /* $whenCondition1 DISCRETE */) /* edge */))
  {
    (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */) = omc_Modelica_Blocks_Tables_Internal_getNextTimeEvent(threadData, (data->simulationInfo->extObjs[2]), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[31]] /* command.timeScaled variable */));
  }
  threadData->lastEquationSolved = 118;
}

/*
equation index: 119
type: SIMPLE_ASSIGN
$cse2 = Modelica.Blocks.Tables.Internal.getTimeTableValueNoDer2(command.tableID, 1, command.timeScaled, command.nextTimeEventScaled, pre(command.nextTimeEventScaled))
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_119(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,119};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[20]] /* $cse2 variable */) = omc_Modelica_Blocks_Tables_Internal_getTimeTableValueNoDer2(threadData, (data->simulationInfo->extObjs[2]), ((modelica_integer) 1), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[31]] /* command.timeScaled variable */), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */), (data->simulationInfo->realVarsPre[85] /* command.nextTimeEventScaled DISCRETE */));
  threadData->lastEquationSolved = 119;
}

/*
equation index: 120
type: SIMPLE_ASSIGN
command.y[1] = command.p_offset[1] + $cse2
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_120(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,120};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[32]] /* command.y[1] variable */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[105]] /* command.p_offset[1] PARAM */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[20]] /* $cse2 variable */);
  threadData->lastEquationSolved = 120;
}

/*
equation index: 121
type: SIMPLE_ASSIGN
$cse1 = min(1.0, command.y[1])
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_121(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,121};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[19]] /* $cse1 variable */) = fmin(1.0,(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[32]] /* command.y[1] variable */));
  threadData->lastEquationSolved = 121;
}

/*
equation index: 122
type: SIMPLE_ASSIGN
bridge.u_lim = max(-1.0, $cse1)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_122(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,122};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[29]] /* bridge.u_lim variable */) = fmax(-1.0,(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[19]] /* $cse1 variable */));
  threadData->lastEquationSolved = 122;
}

/*
equation index: 123
type: SIMPLE_ASSIGN
i_battery = bridge.u_lim * motor.inductor.i
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_123(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,123};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[35]] /* i_battery variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[29]] /* bridge.u_lim variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* motor.inductor.i STATE(1) */));
  threadData->lastEquationSolved = 123;
}

/*
equation index: 124
type: SIMPLE_ASSIGN
bridge.n.i = motor.inductor.i - i_battery
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_124(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,124};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[28]] /* bridge.n.i variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* motor.inductor.i STATE(1) */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[35]] /* i_battery variable */);
  threadData->lastEquationSolved = 124;
}

/*
equation index: 125
type: SIMPLE_ASSIGN
battery.P_chem = battery.U_nom * i_battery
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_125(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,125};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[23]] /* battery.P_chem variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[2]] /* battery.U_nom PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[35]] /* i_battery variable */));
  threadData->lastEquationSolved = 125;
}

/*
equation index: 126
type: SIMPLE_ASSIGN
$DER.battery.E_drawn = battery.P_chem
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_126(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,126};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[8]] /* der(battery.E_drawn) STATE_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[23]] /* battery.P_chem variable */);
  threadData->lastEquationSolved = 126;
}

/*
equation index: 127
type: SIMPLE_ASSIGN
battery.rInt.v = battery.rInt.R_actual * i_battery
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_127(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,127};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[26]] /* battery.rInt.v variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[25]] /* battery.rInt.R_actual variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[35]] /* i_battery variable */));
  threadData->lastEquationSolved = 127;
}

/*
equation index: 128
type: SIMPLE_ASSIGN
battery.v = battery.cell.V - battery.rInt.v
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_128(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,128};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[27]] /* battery.v variable */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[3]] /* battery.cell.V PARAM */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[26]] /* battery.rInt.v variable */);
  threadData->lastEquationSolved = 128;
}

/*
equation index: 129
type: SIMPLE_ASSIGN
battery.P_loss = battery.rInt.v * i_battery
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_129(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,129};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[24]] /* battery.P_loss variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[26]] /* battery.rInt.v variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[35]] /* i_battery variable */));
  threadData->lastEquationSolved = 129;
}

/*
equation index: 130
type: SIMPLE_ASSIGN
bridge.v_mot = bridge.u_lim * battery.v
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_130(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,130};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[30]] /* bridge.v_mot variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[29]] /* bridge.u_lim variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[27]] /* battery.v variable */));
  threadData->lastEquationSolved = 130;
}

/*
equation index: 131
type: SIMPLE_ASSIGN
motor.resistor.n.v = bridge.v_mot - motor.resistor.v
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_131(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,131};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[47]] /* motor.resistor.n.v variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[30]] /* bridge.v_mot variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[48]] /* motor.resistor.v variable */);
  threadData->lastEquationSolved = 131;
}

/*
equation index: 132
type: SIMPLE_ASSIGN
motor.inductor.v = motor.resistor.n.v - motor.emf.v
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_132(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,132};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[45]] /* motor.inductor.v variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[47]] /* motor.resistor.n.v variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[41]] /* motor.emf.v variable */);
  threadData->lastEquationSolved = 132;
}

/*
equation index: 133
type: SIMPLE_ASSIGN
$DER.motor.inductor.i = motor.inductor.v / motor.inductor.L
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_133(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,133};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[15]] /* der(motor.inductor.i) STATE_DER */) = DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[45]] /* motor.inductor.v variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[134]] /* motor.inductor.L PARAM */),"motor.inductor.L",equationIndexes);
  threadData->lastEquationSolved = 133;
}

/*
equation index: 134
type: SIMPLE_ASSIGN
motor.P_el = bridge.v_mot * motor.inductor.i
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_134(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,134};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[37]] /* motor.P_el variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[30]] /* bridge.v_mot variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[7]] /* motor.inductor.i STATE(1) */));
  threadData->lastEquationSolved = 134;
}

/*
equation index: 135
type: WHEN

when {$whenCondition1} then
  command.nextTimeEvent = if command.nextTimeEventScaled < 1e60 then command.nextTimeEventScaled else 1e60;
end when;
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_135(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,135};
  modelica_boolean tmp3;
  if(((data->localData[0]->booleanVars[data->simulationInfo->booleanVarsIndex[0]] /* $whenCondition1 DISCRETE */) && !(data->simulationInfo->booleanVarsPre[0] /* $whenCondition1 DISCRETE */) /* edge */))
  {
    tmp3 = Less((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */),1e60);
    (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[84]] /* command.nextTimeEvent DISCRETE */) = (tmp3?(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[85]] /* command.nextTimeEventScaled DISCRETE */):1e60);
  }
  threadData->lastEquationSolved = 135;
}

/*
equation index: 136
type: SIMPLE_ASSIGN
motor.rotor.phi = motor.housing.phi0 - motor.friction.phi_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_136(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,136};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[51]] /* motor.rotor.phi DUMMY_STATE */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[133]] /* motor.housing.phi0 PARAM */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[5]] /* motor.friction.phi_rel STATE(1,motor.friction.w_rel) */);
  threadData->lastEquationSolved = 136;
}

/*
equation index: 137
type: SIMPLE_ASSIGN
motor.emf.phi = motor.rotor.phi - motor.emf.fixed.phi0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_137(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,137};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[39]] /* motor.emf.phi DUMMY_STATE */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[51]] /* motor.rotor.phi DUMMY_STATE */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[129]] /* motor.emf.fixed.phi0 PARAM */);
  threadData->lastEquationSolved = 137;
}

/*
equation index: 138
type: SIMPLE_ASSIGN
p_R = Modelica.Blocks.Tables.Internal.getTable1DValue(chamberR.pV.tableID, 1, chamberR.V)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_138(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,138};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[54]] /* p_R variable */) = omc_Modelica_Blocks_Tables_Internal_getTable1DValue(threadData, (data->simulationInfo->extObjs[1]), ((modelica_integer) 1), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[4]] /* chamberR.V STATE(1,pipeR.V_flow) */));
  threadData->lastEquationSolved = 138;
}

/*
equation index: 139
type: SIMPLE_ASSIGN
pipeR.port_b.p = chamberR.p_ambient + p_R
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_139(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,139};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[65]] /* pipeR.port_b.p variable */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[81]] /* chamberR.p_ambient PARAM */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[54]] /* p_R variable */);
  threadData->lastEquationSolved = 139;
}

/*
equation index: 140
type: SIMPLE_ASSIGN
p_L = Modelica.Blocks.Tables.Internal.getTable1DValue(chamberL.pV.tableID, 1, chamberL.V)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_140(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,140};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[53]] /* p_L variable */) = omc_Modelica_Blocks_Tables_Internal_getTable1DValue(threadData, (data->simulationInfo->extObjs[0]), ((modelica_integer) 1), (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[2]] /* chamberL.V STATE(1,pipeL.V_flow) */));
  threadData->lastEquationSolved = 140;
}

/*
equation index: 141
type: SIMPLE_ASSIGN
pipeL.port_b.p = chamberL.p_ambient + p_L
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_141(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,141};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[59]] /* pipeL.port_b.p variable */) = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[33]] /* chamberL.p_ambient PARAM */) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[53]] /* p_L variable */);
  threadData->lastEquationSolved = 141;
}

void FishRobot_Examples_HydraulicsStep_eqFunction_142(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_143(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_144(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_145(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_146(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_147(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_148(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_149(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_150(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_151(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_152(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_155(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_154(DATA*, threadData_t*);
void FishRobot_Examples_HydraulicsStep_eqFunction_153(DATA*, threadData_t*);
/*
equation index: 169
indexNonlinear: 1
type: NONLINEAR

vars: {pipeL.V_flow, reliefRL.dp, reliefLR.dp}
eqns: {142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 155, 154, 153}
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_169(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,169};
  int retValue;
  infoStreamPrint(OMC_LOG_DT, 0, "Solving nonlinear system 169 (STRICT TEARING SET if tearing enabled) at time = %18.10e", data->localData[0]->timeValue);
  /* get old value */
  data->simulationInfo->nonlinearSystemData[1].nlsxOld[0] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  data->simulationInfo->nonlinearSystemData[1].nlsxOld[1] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */);
  data->simulationInfo->nonlinearSystemData[1].nlsxOld[2] = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */);
  retValue = solve_nonlinear_system(data, threadData, 1);
  /* check if solution process was successful */
  if (retValue > 0){
    const int indexes[2] = {1,169};
    throwStreamPrintWithEquationIndexes(threadData, omc_dummyFileInfo, indexes, "Solving non-linear system 169 failed at time=%.15g.\nFor more information please use -lv LOG_NLS.", data->localData[0]->timeValue);
  }
  /* write solution */
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */) = data->simulationInfo->nonlinearSystemData[1].nlsx[0];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */) = data->simulationInfo->nonlinearSystemData[1].nlsx[1];
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */) = data->simulationInfo->nonlinearSystemData[1].nlsx[2];
  threadData->lastEquationSolved = 169;
}

/*
equation index: 170
type: SIMPLE_ASSIGN
reliefLR.P_loss = reliefLR.dp * reliefLR.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_170(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,170};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[74]] /* reliefLR.P_loss variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[76]] /* reliefLR.dp variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */));
  threadData->lastEquationSolved = 170;
}

/*
equation index: 171
type: SIMPLE_ASSIGN
reliefRL.P_loss = reliefRL.dp * reliefRL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_171(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,171};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[78]] /* reliefRL.P_loss variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[80]] /* reliefRL.dp variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */));
  threadData->lastEquationSolved = 171;
}

/*
equation index: 172
type: SIMPLE_ASSIGN
Q_relief = reliefLR.V_flow - reliefRL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_172(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,172};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[22]] /* Q_relief variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[75]] /* reliefLR.V_flow variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[79]] /* reliefRL.V_flow variable */);
  threadData->lastEquationSolved = 172;
}

/*
equation index: 173
type: SIMPLE_ASSIGN
pipeR.v = pipeR.V_flow / pipeR.A
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_173(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,173};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[66]] /* pipeR.v variable */) = DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[153]] /* pipeR.A PARAM */),"pipeR.A",equationIndexes);
  threadData->lastEquationSolved = 173;
}

/*
equation index: 174
type: SIMPLE_ASSIGN
pipeR.Re = pipeR.rho * abs(pipeR.v) * pipeR.d / pipeR.mu
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_174(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,174};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[62]] /* pipeR.Re variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[162]] /* pipeR.rho PARAM */)) * ((fabs((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[66]] /* pipeR.v variable */))) * (DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[159]] /* pipeR.d PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[161]] /* pipeR.mu PARAM */),"pipeR.mu",equationIndexes)));
  threadData->lastEquationSolved = 174;
}

/*
equation index: 175
type: SIMPLE_ASSIGN
$DER.chamberR.V = pipeR.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_175(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,175};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[12]] /* der(chamberR.V) STATE_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */);
  threadData->lastEquationSolved = 175;
}

/*
equation index: 176
type: SIMPLE_ASSIGN
$DER.chamberR.E_elastic = p_R * pipeR.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_176(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,176};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[11]] /* der(chamberR.E_elastic) STATE_DER */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[54]] /* p_R variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */));
  threadData->lastEquationSolved = 176;
}

/*
equation index: 177
type: SIMPLE_ASSIGN
pipeR.P_loss = pipeR.dp * pipeR.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_177(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,177};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[61]] /* pipeR.P_loss variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[64]] /* pipeR.dp variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[63]] /* pipeR.V_flow variable */));
  threadData->lastEquationSolved = 177;
}

/*
equation index: 178
type: SIMPLE_ASSIGN
pump.tau_fric = pump.D * abs(pump.dp_pump) * (1.0 + (-1.0) / pump.eta_m) * motor.friction.w_rel / sqrt(motor.friction.w_rel ^ 2.0 + pump.w_small ^ 2.0)
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_178(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,178};
  modelica_real tmp4;
  modelica_real tmp5;
  modelica_real tmp6;
  tmp4 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */);
  tmp5 = (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[168]] /* pump.w_small PARAM */);
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
      throwStreamPrintWithEquationIndexes(threadData, info, equationIndexes, "Model error: Argument of sqrt(motor.friction.w_rel ^ 2.0 + pump.w_small ^ 2.0) was %g should be >= 0", tmp6);
    }
  }
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[73]] /* pump.tau_fric variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[164]] /* pump.D PARAM */)) * ((fabs((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */))) * ((1.0 + DIVISION_SIM(-1.0,(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[166]] /* pump.eta_m PARAM */),"pump.eta_m",equationIndexes)) * (DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */),sqrt(tmp6),"sqrt(motor.friction.w_rel ^ 2.0 + pump.w_small ^ 2.0)",equationIndexes))));
  threadData->lastEquationSolved = 178;
}

/*
equation index: 179
type: SIMPLE_ASSIGN
pump.P_loss_mech = (-pump.tau_fric) * motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_179(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,179};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[69]] /* pump.P_loss_mech variable */) = ((-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[73]] /* pump.tau_fric variable */))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 179;
}

/*
equation index: 180
type: SIMPLE_ASSIGN
pump.flange.tau = pump.D * pump.dp_pump + pump.tau_fric
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_180(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,180};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[72]] /* pump.flange.tau variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[164]] /* pump.D PARAM */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */)) + (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[73]] /* pump.tau_fric variable */);
  threadData->lastEquationSolved = 180;
}

/*
equation index: 181
type: SIMPLE_ASSIGN
pump.P_shaft = (-pump.flange.tau) * motor.friction.w_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_181(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,181};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[70]] /* pump.P_shaft variable */) = ((-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[72]] /* pump.flange.tau variable */))) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[6]] /* motor.friction.w_rel STATE(1,motor.friction.a_rel) */));
  threadData->lastEquationSolved = 181;
}

/*
equation index: 182
type: SIMPLE_ASSIGN
motor.rotor.flange_b.tau = motor.friction.tau - pump.flange.tau
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_182(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,182};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[50]] /* motor.rotor.flange_b.tau variable */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[44]] /* motor.friction.tau variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[72]] /* pump.flange.tau variable */);
  threadData->lastEquationSolved = 182;
}

/*
equation index: 183
type: SIMPLE_ASSIGN
motor.friction.a_rel = (motor.emf.tau - motor.rotor.flange_b.tau) / motor.rotor.J
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_183(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,183};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[43]] /* motor.friction.a_rel variable */) = DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[40]] /* motor.emf.tau variable */) - (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[50]] /* motor.rotor.flange_b.tau variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[140]] /* motor.rotor.J PARAM */),"motor.rotor.J",equationIndexes);
  threadData->lastEquationSolved = 183;
}

/*
equation index: 184
type: SIMPLE_ASSIGN
$DER.motor.friction.w_rel = motor.friction.a_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_184(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,184};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[14]] /* der(motor.friction.w_rel) STATE_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[43]] /* motor.friction.a_rel variable */);
  threadData->lastEquationSolved = 184;
}

/*
equation index: 185
type: SIMPLE_ASSIGN
$DER.motor.rotor.w = -motor.friction.a_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_185(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,185};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[18]] /* der(motor.rotor.w) DUMMY_DER */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[43]] /* motor.friction.a_rel variable */));
  threadData->lastEquationSolved = 185;
}

/*
equation index: 186
type: SIMPLE_ASSIGN
motor.rotor.a = -motor.friction.a_rel
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_186(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,186};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[49]] /* motor.rotor.a variable */) = (-(data->localData[0]->realVars[data->simulationInfo->realVarsIndex[43]] /* motor.friction.a_rel variable */));
  threadData->lastEquationSolved = 186;
}

/*
equation index: 187
type: SIMPLE_ASSIGN
pump.P_loss_leak = pump.k_leak * pump.dp_pump ^ 2.0
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_187(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,187};
  modelica_real tmp7;
  tmp7 = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */);
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[68]] /* pump.P_loss_leak variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[167]] /* pump.k_leak PARAM */)) * ((tmp7 * tmp7));
  threadData->lastEquationSolved = 187;
}

/*
equation index: 188
type: SIMPLE_ASSIGN
pump.P_hyd = pump.dp_pump * Q_pump
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_188(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,188};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[67]] /* pump.P_hyd variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[71]] /* pump.dp_pump variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[21]] /* Q_pump variable */));
  threadData->lastEquationSolved = 188;
}

/*
equation index: 189
type: SIMPLE_ASSIGN
pipeL.v = pipeL.V_flow / pipeL.A
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_189(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,189};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[60]] /* pipeL.v variable */) = DIVISION_SIM((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[142]] /* pipeL.A PARAM */),"pipeL.A",equationIndexes);
  threadData->lastEquationSolved = 189;
}

/*
equation index: 190
type: SIMPLE_ASSIGN
pipeL.Re = pipeL.rho * abs(pipeL.v) * pipeL.d / pipeL.mu
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_190(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,190};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[56]] /* pipeL.Re variable */) = ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[151]] /* pipeL.rho PARAM */)) * ((fabs((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[60]] /* pipeL.v variable */))) * (DIVISION_SIM((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[148]] /* pipeL.d PARAM */),(data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[150]] /* pipeL.mu PARAM */),"pipeL.mu",equationIndexes)));
  threadData->lastEquationSolved = 190;
}

/*
equation index: 191
type: SIMPLE_ASSIGN
$DER.chamberL.V = pipeL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_191(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,191};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[10]] /* der(chamberL.V) STATE_DER */) = (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */);
  threadData->lastEquationSolved = 191;
}

/*
equation index: 192
type: SIMPLE_ASSIGN
pipeL.P_loss = pipeL.dp * pipeL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_192(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,192};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[55]] /* pipeL.P_loss variable */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[58]] /* pipeL.dp variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */));
  threadData->lastEquationSolved = 192;
}

/*
equation index: 193
type: SIMPLE_ASSIGN
$DER.chamberL.E_elastic = p_L * pipeL.V_flow
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_193(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,193};
  (data->localData[0]->realVars[data->simulationInfo->realVarsIndex[9]] /* der(chamberL.E_elastic) STATE_DER */) = ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[53]] /* p_L variable */)) * ((data->localData[0]->realVars[data->simulationInfo->realVarsIndex[57]] /* pipeL.V_flow variable */));
  threadData->lastEquationSolved = 193;
}

/*
equation index: 195
type: ALGORITHM

  assert(1.0 + battery.rInt.alpha * (battery.rInt.T - battery.rInt.T_ref) >= 2.220446049250313e-16, "Temperature outside scope of model!");
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_195(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,195};
  modelica_boolean tmp8;
  static const MMC_DEFSTRINGLIT(tmp9,35,"Temperature outside scope of model!");
  static int tmp10 = 0;
  {
    tmp8 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[7]] /* battery.rInt.alpha PARAM */)) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[5]] /* battery.rInt.T PARAM */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[6]] /* battery.rInt.T_ref PARAM */)),2.220446049250313e-16);
    if(!tmp8)
    {
      {
        const char* assert_cond = "(1.0 + battery.rInt.alpha * (battery.rInt.T - battery.rInt.T_ref) >= 2.220446049250313e-16)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp9)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp9)));
        }
      }
    }
  }
  threadData->lastEquationSolved = 195;
}

/*
equation index: 194
type: ALGORITHM

  assert(1.0 + motor.resistor.alpha * (motor.resistor.T - motor.resistor.T_ref) >= 2.220446049250313e-16, "Temperature outside scope of model!");
*/
void FishRobot_Examples_HydraulicsStep_eqFunction_194(DATA *data, threadData_t *threadData)
{
  const int equationIndexes[2] = {1,194};
  modelica_boolean tmp11;
  static const MMC_DEFSTRINGLIT(tmp12,35,"Temperature outside scope of model!");
  static int tmp13 = 0;
  {
    tmp11 = GreaterEq(1.0 + ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[139]] /* motor.resistor.alpha PARAM */)) * ((data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[137]] /* motor.resistor.T PARAM */) - (data->simulationInfo->realParameter[data->simulationInfo->realParamsIndex[138]] /* motor.resistor.T_ref PARAM */)),2.220446049250313e-16);
    if(!tmp11)
    {
      {
        const char* assert_cond = "(1.0 + motor.resistor.alpha * (motor.resistor.T - motor.resistor.T_ref) >= 2.220446049250313e-16)";
        if (data->simulationInfo->noThrowAsserts) {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          infoStreamPrintWithEquationIndexes(OMC_LOG_ASSERT, info, 0, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp12)));
          data->simulationInfo->needToReThrow = 1;
        } else {
          FILE_INFO info = {"/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om/Electrical/Analog/Basic/Resistor.mo",15,3,16,43,0};
          omc_assert_withEquationIndexes(threadData, info, equationIndexes, "The following assertion has been violated %sat time %f\n(%s) --> \"%s\"", initial() ? "during initialization " : "", data->localData[0]->timeValue, assert_cond, MMC_STRINGDATA(MMC_REFSTRINGLIT(tmp12)));
        }
      }
    }
  }
  threadData->lastEquationSolved = 194;
}

OMC_DISABLE_OPT
int FishRobot_Examples_HydraulicsStep_functionDAE(DATA *data, threadData_t *threadData)
{
  int equationIndexes[1] = {0};
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_DAE);
#endif

  data->simulationInfo->needToIterate = 0;
  data->simulationInfo->discreteCall = 1;
  FishRobot_Examples_HydraulicsStep_functionLocalKnownVars(data, threadData);
  static void (*const eqFunctions[65])(DATA*, threadData_t*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_104,
    FishRobot_Examples_HydraulicsStep_eqFunction_105,
    FishRobot_Examples_HydraulicsStep_eqFunction_106,
    FishRobot_Examples_HydraulicsStep_eqFunction_107,
    FishRobot_Examples_HydraulicsStep_eqFunction_108,
    FishRobot_Examples_HydraulicsStep_eqFunction_109,
    FishRobot_Examples_HydraulicsStep_eqFunction_110,
    FishRobot_Examples_HydraulicsStep_eqFunction_111,
    FishRobot_Examples_HydraulicsStep_eqFunction_112,
    FishRobot_Examples_HydraulicsStep_eqFunction_113,
    FishRobot_Examples_HydraulicsStep_eqFunction_114,
    FishRobot_Examples_HydraulicsStep_eqFunction_115,
    FishRobot_Examples_HydraulicsStep_eqFunction_116,
    FishRobot_Examples_HydraulicsStep_eqFunction_117,
    FishRobot_Examples_HydraulicsStep_eqFunction_118,
    FishRobot_Examples_HydraulicsStep_eqFunction_119,
    FishRobot_Examples_HydraulicsStep_eqFunction_120,
    FishRobot_Examples_HydraulicsStep_eqFunction_121,
    FishRobot_Examples_HydraulicsStep_eqFunction_122,
    FishRobot_Examples_HydraulicsStep_eqFunction_123,
    FishRobot_Examples_HydraulicsStep_eqFunction_124,
    FishRobot_Examples_HydraulicsStep_eqFunction_125,
    FishRobot_Examples_HydraulicsStep_eqFunction_126,
    FishRobot_Examples_HydraulicsStep_eqFunction_127,
    FishRobot_Examples_HydraulicsStep_eqFunction_128,
    FishRobot_Examples_HydraulicsStep_eqFunction_129,
    FishRobot_Examples_HydraulicsStep_eqFunction_130,
    FishRobot_Examples_HydraulicsStep_eqFunction_131,
    FishRobot_Examples_HydraulicsStep_eqFunction_132,
    FishRobot_Examples_HydraulicsStep_eqFunction_133,
    FishRobot_Examples_HydraulicsStep_eqFunction_134,
    FishRobot_Examples_HydraulicsStep_eqFunction_135,
    FishRobot_Examples_HydraulicsStep_eqFunction_136,
    FishRobot_Examples_HydraulicsStep_eqFunction_137,
    FishRobot_Examples_HydraulicsStep_eqFunction_138,
    FishRobot_Examples_HydraulicsStep_eqFunction_139,
    FishRobot_Examples_HydraulicsStep_eqFunction_140,
    FishRobot_Examples_HydraulicsStep_eqFunction_141,
    FishRobot_Examples_HydraulicsStep_eqFunction_169,
    FishRobot_Examples_HydraulicsStep_eqFunction_170,
    FishRobot_Examples_HydraulicsStep_eqFunction_171,
    FishRobot_Examples_HydraulicsStep_eqFunction_172,
    FishRobot_Examples_HydraulicsStep_eqFunction_173,
    FishRobot_Examples_HydraulicsStep_eqFunction_174,
    FishRobot_Examples_HydraulicsStep_eqFunction_175,
    FishRobot_Examples_HydraulicsStep_eqFunction_176,
    FishRobot_Examples_HydraulicsStep_eqFunction_177,
    FishRobot_Examples_HydraulicsStep_eqFunction_178,
    FishRobot_Examples_HydraulicsStep_eqFunction_179,
    FishRobot_Examples_HydraulicsStep_eqFunction_180,
    FishRobot_Examples_HydraulicsStep_eqFunction_181,
    FishRobot_Examples_HydraulicsStep_eqFunction_182,
    FishRobot_Examples_HydraulicsStep_eqFunction_183,
    FishRobot_Examples_HydraulicsStep_eqFunction_184,
    FishRobot_Examples_HydraulicsStep_eqFunction_185,
    FishRobot_Examples_HydraulicsStep_eqFunction_186,
    FishRobot_Examples_HydraulicsStep_eqFunction_187,
    FishRobot_Examples_HydraulicsStep_eqFunction_188,
    FishRobot_Examples_HydraulicsStep_eqFunction_189,
    FishRobot_Examples_HydraulicsStep_eqFunction_190,
    FishRobot_Examples_HydraulicsStep_eqFunction_191,
    FishRobot_Examples_HydraulicsStep_eqFunction_192,
    FishRobot_Examples_HydraulicsStep_eqFunction_193,
    FishRobot_Examples_HydraulicsStep_eqFunction_195,
    FishRobot_Examples_HydraulicsStep_eqFunction_194
  };
  
  for (int id = 0; id < 65; id++) {
    eqFunctions[id](data, threadData);
  }
  data->simulationInfo->discreteCall = 0;
  
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_DAE);
#endif
  return 0;
}


int FishRobot_Examples_HydraulicsStep_functionLocalKnownVars(DATA *data, threadData_t *threadData)
{
  
  return 0;
}

/* forwarded equations */
extern void FishRobot_Examples_HydraulicsStep_eqFunction_109(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_111(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_112(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_113(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_115(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_116(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_117(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_119(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_120(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_121(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_122(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_123(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_125(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_126(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_127(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_128(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_130(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_131(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_132(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_133(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_138(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_139(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_140(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_141(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_169(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_175(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_176(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_178(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_180(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_182(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_183(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_184(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_191(DATA* data, threadData_t *threadData);
extern void FishRobot_Examples_HydraulicsStep_eqFunction_193(DATA* data, threadData_t *threadData);

static void functionODE_system0(DATA *data, threadData_t *threadData)
{
  static void (*const eqFunctions[34])(DATA*, threadData_t*) = {
    FishRobot_Examples_HydraulicsStep_eqFunction_109,
    FishRobot_Examples_HydraulicsStep_eqFunction_111,
    FishRobot_Examples_HydraulicsStep_eqFunction_112,
    FishRobot_Examples_HydraulicsStep_eqFunction_113,
    FishRobot_Examples_HydraulicsStep_eqFunction_115,
    FishRobot_Examples_HydraulicsStep_eqFunction_116,
    FishRobot_Examples_HydraulicsStep_eqFunction_117,
    FishRobot_Examples_HydraulicsStep_eqFunction_119,
    FishRobot_Examples_HydraulicsStep_eqFunction_120,
    FishRobot_Examples_HydraulicsStep_eqFunction_121,
    FishRobot_Examples_HydraulicsStep_eqFunction_122,
    FishRobot_Examples_HydraulicsStep_eqFunction_123,
    FishRobot_Examples_HydraulicsStep_eqFunction_125,
    FishRobot_Examples_HydraulicsStep_eqFunction_126,
    FishRobot_Examples_HydraulicsStep_eqFunction_127,
    FishRobot_Examples_HydraulicsStep_eqFunction_128,
    FishRobot_Examples_HydraulicsStep_eqFunction_130,
    FishRobot_Examples_HydraulicsStep_eqFunction_131,
    FishRobot_Examples_HydraulicsStep_eqFunction_132,
    FishRobot_Examples_HydraulicsStep_eqFunction_133,
    FishRobot_Examples_HydraulicsStep_eqFunction_138,
    FishRobot_Examples_HydraulicsStep_eqFunction_139,
    FishRobot_Examples_HydraulicsStep_eqFunction_140,
    FishRobot_Examples_HydraulicsStep_eqFunction_141,
    FishRobot_Examples_HydraulicsStep_eqFunction_169,
    FishRobot_Examples_HydraulicsStep_eqFunction_175,
    FishRobot_Examples_HydraulicsStep_eqFunction_176,
    FishRobot_Examples_HydraulicsStep_eqFunction_178,
    FishRobot_Examples_HydraulicsStep_eqFunction_180,
    FishRobot_Examples_HydraulicsStep_eqFunction_182,
    FishRobot_Examples_HydraulicsStep_eqFunction_183,
    FishRobot_Examples_HydraulicsStep_eqFunction_184,
    FishRobot_Examples_HydraulicsStep_eqFunction_191,
    FishRobot_Examples_HydraulicsStep_eqFunction_193
  };
  
  if (data->simulationInfo->evalSelection) {
    for (int i = 0; i < data->simulationInfo->evalSelection->n; i++) {
      int id = data->simulationInfo->evalSelection->idx[i];
      eqFunctions[id](data, threadData);
    }
  } else {
    for (int id = 0; id < 34; id++) {
      eqFunctions[id](data, threadData);
    }
  }
}

int FishRobot_Examples_HydraulicsStep_functionODE(DATA *data, threadData_t *threadData)
{
#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_tick(SIM_TIMER_FUNCTION_ODE);
#endif

  
  data->simulationInfo->callStatistics.functionODE++;
  
  FishRobot_Examples_HydraulicsStep_functionLocalKnownVars(data, threadData);
  functionODE_system0(data, threadData);

#if !defined(OMC_MINIMAL_RUNTIME)
  if (measure_time_flag) rt_accumulate(SIM_TIMER_FUNCTION_ODE);
#endif

  return 0;
}

void FishRobot_Examples_HydraulicsStep_ODE_DAG(DATA* data, threadData_t* threadData)
{
  const size_t eqMap[] = {109, 111, 112, 113, 115, 116, 117, 119, 120, 121, 122, 123, 125, 126, 127, 128, 130, 131, 132, 133, 138, 139, 140, 141, 169, 175, 176, 178, 180, 182, 183, 184, 191, 193};
  buildEvalDAG_ODE(data->modelData, sizeof(eqMap)/sizeof(size_t), eqMap);
}

/* forward the main in the simulation runtime */
extern int _main_SimulationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);
extern int _main_OptimizationRuntime(int argc, char **argv, DATA *data, threadData_t *threadData);

#include "FishRobot.Examples.HydraulicsStep_12jac.h"
#include "FishRobot.Examples.HydraulicsStep_13opt.h"

struct OpenModelicaGeneratedFunctionCallbacks FishRobot_Examples_HydraulicsStep_callback = {
  (int (*)(DATA *, threadData_t *, void *)) FishRobot_Examples_HydraulicsStep_performSimulation,    /* performSimulation */
  (int (*)(DATA *, threadData_t *, void *)) FishRobot_Examples_HydraulicsStep_performQSSSimulation,    /* performQSSSimulation */
  FishRobot_Examples_HydraulicsStep_updateContinuousSystem,    /* updateContinuousSystem */
  FishRobot_Examples_HydraulicsStep_callExternalObjectDestructors,    /* callExternalObjectDestructors */
  FishRobot_Examples_HydraulicsStep_initialNonLinearSystem,    /* initialNonLinearSystem */
  NULL,    /* initialLinearSystem */
  NULL,    /* initialMixedSystem */
  #if !defined(OMC_NO_STATESELECTION)
  FishRobot_Examples_HydraulicsStep_initializeStateSets,
  #else
  NULL,
  #endif    /* initializeStateSets */
  FishRobot_Examples_HydraulicsStep_initializeDAEmodeData,
  FishRobot_Examples_HydraulicsStep_ODE_DAG,
  FishRobot_Examples_HydraulicsStep_functionODE,
  FishRobot_Examples_HydraulicsStep_functionAlgebraics,
  FishRobot_Examples_HydraulicsStep_functionDAE,
  FishRobot_Examples_HydraulicsStep_functionLocalKnownVars,
  FishRobot_Examples_HydraulicsStep_input_function,
  FishRobot_Examples_HydraulicsStep_input_function_init,
  FishRobot_Examples_HydraulicsStep_input_function_updateStartValues,
  FishRobot_Examples_HydraulicsStep_data_function,
  FishRobot_Examples_HydraulicsStep_output_function,
  FishRobot_Examples_HydraulicsStep_setc_function,
  FishRobot_Examples_HydraulicsStep_setb_function,
  FishRobot_Examples_HydraulicsStep_function_storeDelayed,
  FishRobot_Examples_HydraulicsStep_function_storeSpatialDistribution,
  FishRobot_Examples_HydraulicsStep_function_initSpatialDistribution,
  FishRobot_Examples_HydraulicsStep_updateBoundVariableAttributes,
  FishRobot_Examples_HydraulicsStep_functionInitialEquations,
  GLOBAL_EQUIDISTANT_HOMOTOPY,
  NULL,
  FishRobot_Examples_HydraulicsStep_functionRemovedInitialEquations,
  FishRobot_Examples_HydraulicsStep_updateBoundParameters,
  FishRobot_Examples_HydraulicsStep_checkForAsserts,
  FishRobot_Examples_HydraulicsStep_function_ZeroCrossingsEquations,
  FishRobot_Examples_HydraulicsStep_function_ZeroCrossings,
  FishRobot_Examples_HydraulicsStep_function_updateRelations,
  FishRobot_Examples_HydraulicsStep_zeroCrossingDescription,
  FishRobot_Examples_HydraulicsStep_relationDescription,
  FishRobot_Examples_HydraulicsStep_function_initSample,
  FishRobot_Examples_HydraulicsStep_INDEX_JAC_A,
  FishRobot_Examples_HydraulicsStep_INDEX_JAC_ADJ,
  FishRobot_Examples_HydraulicsStep_INDEX_JAC_B,
  FishRobot_Examples_HydraulicsStep_INDEX_JAC_C,
  FishRobot_Examples_HydraulicsStep_INDEX_JAC_D,
  FishRobot_Examples_HydraulicsStep_INDEX_JAC_F,
  FishRobot_Examples_HydraulicsStep_INDEX_JAC_H,
  FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianA,
  FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianADJ,
  FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianB,
  FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianC,
  FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianD,
  FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianF,
  FishRobot_Examples_HydraulicsStep_initialAnalyticJacobianH,
  FishRobot_Examples_HydraulicsStep_functionJacA_column,
  FishRobot_Examples_HydraulicsStep_functionJacADJ_column,
  FishRobot_Examples_HydraulicsStep_functionJacB_column,
  FishRobot_Examples_HydraulicsStep_functionJacC_column,
  FishRobot_Examples_HydraulicsStep_functionJacD_column,
  FishRobot_Examples_HydraulicsStep_functionJacF_column,
  FishRobot_Examples_HydraulicsStep_functionJacH_column,
  FishRobot_Examples_HydraulicsStep_JacA_DAG,
  FishRobot_Examples_HydraulicsStep_linear_model_frame,
  FishRobot_Examples_HydraulicsStep_linear_model_datarecovery_frame,
  FishRobot_Examples_HydraulicsStep_mayer,
  FishRobot_Examples_HydraulicsStep_lagrange,
  FishRobot_Examples_HydraulicsStep_getInputVarIndicesInOptimization,
  FishRobot_Examples_HydraulicsStep_pickUpBoundsForInputsInOptimization,
  FishRobot_Examples_HydraulicsStep_setInputData,
  FishRobot_Examples_HydraulicsStep_getTimeGrid,
  FishRobot_Examples_HydraulicsStep_symbolicInlineSystem,
  FishRobot_Examples_HydraulicsStep_function_initSynchronous,
  FishRobot_Examples_HydraulicsStep_function_updateSynchronous,
  FishRobot_Examples_HydraulicsStep_function_equationsSynchronous,
  FishRobot_Examples_HydraulicsStep_inputNames,
  FishRobot_Examples_HydraulicsStep_dataReconciliationInputNames,
  FishRobot_Examples_HydraulicsStep_dataReconciliationUnmeasuredVariables,
  NULL,
  NULL,
  NULL,
  NULL,
  -1,
  NULL,
  NULL,
  -1

};

#define _OMC_LIT_RESOURCE_0_name_data "Complex"
#define _OMC_LIT_RESOURCE_0_dir_data "/home/leo-morph/.openmodelica/libraries/Complex 4.1.0+maint.om"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_name,7,_OMC_LIT_RESOURCE_0_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir,62,_OMC_LIT_RESOURCE_0_dir_data);

#define _OMC_LIT_RESOURCE_1_name_data "FishRobot"
#define _OMC_LIT_RESOURCE_1_dir_data "/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_1_name,9,_OMC_LIT_RESOURCE_1_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_1_dir,54,_OMC_LIT_RESOURCE_1_dir_data);

#define _OMC_LIT_RESOURCE_2_name_data "Modelica"
#define _OMC_LIT_RESOURCE_2_dir_data "/home/leo-morph/.openmodelica/libraries/Modelica 4.1.0+maint.om"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_2_name,8,_OMC_LIT_RESOURCE_2_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_2_dir,63,_OMC_LIT_RESOURCE_2_dir_data);

#define _OMC_LIT_RESOURCE_3_name_data "ModelicaServices"
#define _OMC_LIT_RESOURCE_3_dir_data "/home/leo-morph/.openmodelica/libraries/ModelicaServices 4.1.0+maint.om"
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_3_name,16,_OMC_LIT_RESOURCE_3_name_data);
static const MMC_DEFSTRINGLIT(_OMC_LIT_RESOURCE_3_dir,71,_OMC_LIT_RESOURCE_3_dir_data);

static const MMC_DEFSTRUCTLIT(_OMC_LIT_RESOURCES,8,MMC_ARRAY_TAG) {MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_0_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_1_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_1_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_2_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_2_dir), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_3_name), MMC_REFSTRINGLIT(_OMC_LIT_RESOURCE_3_dir)}};
void FishRobot_Examples_HydraulicsStep_setupDataStruc(DATA *data, threadData_t *threadData)
{
  assertStreamPrint(threadData,0!=data, "Error while initialize Data");
  threadData->localRoots[LOCAL_ROOT_SIMULATION_DATA] = data;
  data->callback = &FishRobot_Examples_HydraulicsStep_callback;
  OpenModelica_updateUriMapping(threadData, MMC_REFSTRUCTLIT(_OMC_LIT_RESOURCES));
  data->modelData->modelName = "FishRobot.Examples.HydraulicsStep";
  data->modelData->modelFilePrefix = "FishRobot.Examples.HydraulicsStep";
  data->modelData->modelFileName = "HydraulicsStep.mo";
  data->modelData->resultFileName = NULL;
  data->modelData->modelDir = "/home/leo-morph/Dokumenty/GitHub/fish-sim-v0/FishRobot/Examples";
  data->modelData->modelGUID = "{90cb5248-5739-4a29-a2f4-14eb1c654b16}";
  #if defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME)
  data->modelData->initXMLData = NULL;
  data->modelData->modelDataXml.infoXMLData = NULL;
  #else
  #if defined(_MSC_VER) /* handle joke compilers */
  {
  /* for MSVC we encode a string like char x[] = {'a', 'b', 'c', '\0'} */
  /* because the string constant limit is 65535 bytes */
  static const char contents_init[] =
    #include "FishRobot.Examples.HydraulicsStep_init.c"
    ;
  static const char contents_info[] =
    #include "FishRobot.Examples.HydraulicsStep_info.c"
    ;
    data->modelData->initXMLData = contents_init;
    data->modelData->modelDataXml.infoXMLData = contents_info;
  }
  #else /* handle real compilers */
  data->modelData->initXMLData =
  #include "FishRobot.Examples.HydraulicsStep_init.c"
    ;
  data->modelData->modelDataXml.infoXMLData =
  #include "FishRobot.Examples.HydraulicsStep_info.c"
    ;
  #endif /* defined(_MSC_VER) */
  #endif /* defined(OPENMODELICA_XML_FROM_FILE_AT_RUNTIME) */
  data->modelData->modelDataXml.fileName = "FishRobot.Examples.HydraulicsStep_info.json";
  data->modelData->resourcesDir = NULL;
  data->modelData->runTestsuite = 0;
  data->modelData->nStatesArray = 8;
  data->modelData->nDiscreteReal = 2;
  data->modelData->nVariablesRealArray = 86;
  data->modelData->nVariablesIntegerArray = 0;
  data->modelData->nVariablesBooleanArray = 1;
  data->modelData->nVariablesStringArray = 0;
  data->modelData->nParametersRealArray = 181;
  data->modelData->nParametersIntegerArray = 20;
  data->modelData->nParametersBooleanArray = 20;
  data->modelData->nParametersStringArray = 13;
  data->modelData->nParametersReal = 181;
  data->modelData->nParametersInteger = 20;
  data->modelData->nParametersBoolean = 20;
  data->modelData->nParametersString = 13;
  data->modelData->nAliasRealArray = 104;
  data->modelData->nAliasIntegerArray = 0;
  data->modelData->nAliasBooleanArray = 0;
  data->modelData->nAliasStringArray = 0;
  data->modelData->nInputVars = 0;
  data->modelData->nOutputVars = 0;
  data->modelData->nZeroCrossings = 1;
  data->modelData->nSamples = 0;
  data->modelData->nRelations = 1;
  data->modelData->nMathEvents = 0;
  data->modelData->nExtObjs = 3;
  data->modelData->modelDataXml.modelInfoXmlLength = 0;
  data->modelData->modelDataXml.nFunctions = 11;
  data->modelData->modelDataXml.nProfileBlocks = 0;
  data->modelData->modelDataXml.nEquations = 361;
  data->modelData->nMixedSystems = 0;
  data->modelData->nLinearSystems = 0;
  data->modelData->nNonLinearSystems = 2;
  data->modelData->nStateSets = 0;
  data->modelData->nJacobians = 9;
  data->modelData->nOptimizeConstraints = 0;
  data->modelData->nOptimizeFinalConstraints = 0;
  data->modelData->nDelayExpressions = 0;
  data->modelData->nBaseClocks = 0;
  data->modelData->nSpatialDistributions = 0;
  data->modelData->nSensitivityVars = 0;
  data->modelData->nSensitivityParamVars = 0;
  data->modelData->nSetcVars = 0;
  data->modelData->ndataReconVars = 0;
  data->modelData->nSetbVars = 0;
  data->modelData->nRelatedBoundaryConditions = 0;
  data->modelData->linearizationDumpLanguage = OMC_LINEARIZE_DUMP_LANGUAGE_MODELICA;
}

static int rml_execution_failed()
{
  fflush(NULL);
  fprintf(stderr, "Execution failed!\n");
  fflush(NULL);
  return 1;
}


#if defined(__MINGW32__) || defined(_MSC_VER)

#if !defined(_UNICODE)
#define _UNICODE
#endif
#if !defined(UNICODE)
#define UNICODE
#endif

#include <windows.h>
char** omc_fixWindowsArgv(int argc, wchar_t **wargv)
{
  char** newargv;
  /* Support for non-ASCII characters
  * Read the unicode command line arguments and translate it to char*
  */
  newargv = (char**)malloc(argc*sizeof(char*));
  for (int i = 0; i < argc; i++) {
    newargv[i] = omc_wchar_to_multibyte_str(wargv[i]);
  }
  return newargv;
}

#define OMC_MAIN wmain
#define OMC_CHAR wchar_t
#define OMC_EXPORT __declspec(dllexport) extern

#else
#define omc_fixWindowsArgv(N, A) (A)
#define OMC_MAIN main
#define OMC_CHAR char
#define OMC_EXPORT extern
#endif

#if defined(threadData)
#undef threadData
#endif
/* call the simulation runtime main from our main! */
#if defined(OMC_DLL_MAIN_DEFINE)
OMC_EXPORT int omcDllMain(int argc, OMC_CHAR **argv)
#else
int OMC_MAIN(int argc, OMC_CHAR** argv)
#endif
{
  char** newargv = omc_fixWindowsArgv(argc, argv);
  /*
    Set the error functions to be used for simulation.
    The default value for them is 'functions' version. Change it here to 'simulation' versions
  */
  omc_assert = omc_assert_simulation;
  omc_assert_withEquationIndexes = omc_assert_simulation_withEquationIndexes;

  omc_assert_warning_withEquationIndexes = omc_assert_warning_simulation_withEquationIndexes;
  omc_assert_warning = omc_assert_warning_simulation;
  omc_terminate = omc_terminate_simulation;
  omc_throw = omc_throw_simulation;

  int res;
  DATA data;
  MODEL_DATA modelData;
  SIMULATION_INFO simInfo;
  data.modelData = &modelData;
  data.simulationInfo = &simInfo;
  measure_time_flag = 0;
  compiledInDAEMode = 0;
  compiledWithSymSolver = 0;
  MMC_INIT(0);
  omc_alloc_interface.init();
  {
    MMC_TRY_TOP()
  
    MMC_TRY_STACK()
  
    FishRobot_Examples_HydraulicsStep_setupDataStruc(&data, threadData);
    res = _main_initRuntimeAndSimulation(argc, newargv, &data, threadData);
    if(res == 0) {
      if (omc_flag[FLAG_MOO_OPTIMIZATION]) {
        res = _main_OptimizationRuntime(argc, newargv, &data, threadData);
      } else {
        res = _main_SimulationRuntime(argc, newargv, &data, threadData);
      }
    }
    
    MMC_ELSE()
    rml_execution_failed();
    fprintf(stderr, "Stack overflow detected and was not caught.\nSend us a bug report at https://trac.openmodelica.org/OpenModelica/newticket\n    Include the following trace:\n");
    printStacktraceMessages();
    fflush(NULL);
    return 1;
    MMC_CATCH_STACK()
    
    MMC_CATCH_TOP(return rml_execution_failed());
  }

  fflush(NULL);
  return res;
}

#ifdef __cplusplus
}
#endif


