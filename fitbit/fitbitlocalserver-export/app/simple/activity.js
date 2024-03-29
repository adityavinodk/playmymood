import * as messaging from "messaging";
import { me } from "appbit";
import clock from "clock";
import { today, goals } from "user-activity";
import { units } from "user-settings";
import * as util from "../../common/utils";
let activityCallback;

export function initialize(granularity, callback) {
  if (me.permissions.granted("access_activity")) {
    var steps = getSteps();
    var calories = getCalories();
    var distance = getDistance();
    var elevationGain = getElevationGain();
    var activeMinutes = getActiveMinutes();
    clock.granularity = granularity;
    clock.addEventListener("tick", tickHandler);
    activityCallback = callback;
  } else {
    console.log("Denied User Activity permission");
    callback({
      steps: getDeniedStats(),
      calories: getDeniedStats(),
      distance: getDeniedStats(),
      elevationGain: getDeniedStats(),
      activeMinutes: getDeniedStats(),
    });
  }
}

let activityData = () => {
  return {
    steps: getSteps(),
    calories: getCalories(),
    distance: getDistance(),
    elevationGain: getElevationGain(),
    activeMinutes: getActiveMinutes(),
  };
};
function tickHandler(evt) {
  var activity = activityData();
  var data = {
    steps: activity.steps.raw,
    calories: activity.calories.raw,
    distance: activity.distance.raw,
    elevationGain: activity.elevationGain.raw,
    activeMinutes: activity.activeMinutes.raw,
    timestamp: util.formatDate(new Date()),
  };
  //util.sendToServer({'key':'activity','data':data});
  activityCallback(activityData());
}

function getActiveMinutes() {
  let val = today.adjusted.activeMinutes || 0;
  return {
    raw: val,
    pretty:
      (val < 60 ? "" : Math.floor(val / 60) + "h,") +
      ("0" + (val % 60)).slice("-2") +
      "m",
  };
}

function getCalories() {
  let val = today.adjusted.calories || 0;
  return {
    raw: val,
    pretty:
      val > 999
        ? Math.floor(val / 1000) + "," + ("00" + (val % 1000)).slice(-3)
        : val,
  };
}

function getDistance() {
  let val = (today.adjusted.distance || 0) / 1000;
  let u = "km";
  if (units.distance === "us") {
    val *= 0.621371;
    u = "mi";
  }
  return {
    raw: val,
    pretty: `${val.toFixed(2)}${u}`,
  };
}

function getElevationGain() {
  let val = today.adjusted.elevationGain || 0;
  return {
    raw: val,
    pretty: `+${val}`,
  };
}

function getSteps() {
  let val = today.adjusted.steps || 0;
  return {
    raw: val,
    pretty:
      val > 999
        ? Math.floor(val / 1000) + "," + ("00" + (val % 1000)).slice(-3)
        : val,
  };
}

function getDeniedStats() {
  return {
    raw: 0,
    pretty: "Denied",
  };
}
