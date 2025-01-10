'use strict';

import { micboard, ActivateMessageBoard, updateHash } from './app.js';
import { updateBackground } from './gif.js';
import { initChart, charts } from './chart-smoothie.js';
import { seedTransmitters, autoRandom } from './demodata.js';
import { updateEditor } from './dnd.js';

function allSlots() {
  const slot = micboard.config.slots;
  const out = [];

  if (micboard.url.demo) {
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
  }

  for (let i = 0; i < slot.length; i += 1) {
    out.push(slot[i].slot);
  }
  return out;
}


// enables info-drawer toggle for mobile clients
function infoToggle() {
  const cols = document.getElementsByClassName('col-sm')
  Array.from(cols).forEach((element) => {
    element.addEventListener('click', (e) => {
      if (window.innerWidth <= 980 && micboard.settingsMode !== 'EXTENDED') {
        const id = e.currentTarget.querySelector('.info-drawer')
        if (id.style.display == 'none' || id.style.display == '') {
          id.style.display = 'block';
        } else if (id.style.display == 'block' ){
          id.style.display = 'none'
        }
      }
    })
  })

  if (micboard.group === 0) {
    document.getElementById('go-groupedit').style.display = 'none'
  } else if (micboard.group !== 0) {
    document.getElementById('go-groupedit').style.display = 'block'
  }
}

function updateTXOffset(slotSelector, data) {
  if (data.tx_offset !== 255) {
    slotSelector.querySelector('p.offset').innerHTML = data.tx_offset + ' dB';
  } else {
    slotSelector.querySelector('p.offset').innerHTML = '';
  }
}


function updateRuntime(slotSelector, data) {
  slotSelector.querySelector('p.runtime').innerHTML = data.runtime;
}

function updatePowerlock(slotSelector, data) {
  if (data.power_lock === 'ON') {
    slotSelector.querySelector('p.powerlock').style.display = 'block';
  } else {
    slotSelector.querySelector('p.powerlock').style.display = 'none';
  }


}

function updateQuality(slotSelector, data) {
  const QualityTable = {
    0: '&#9675;&#9675;&#9675;&#9675;&#9675;',
    1: '&#9679;&#9675;&#9675;&#9675;&#9675;',
    2: '&#9679;&#9679;&#9675;&#9675;&#9675;',
    3: '&#9679;&#9679;&#9679;&#9675;&#9675;',
    4: '&#9679;&#9679;&#9679;&#9679;&#9675;',
    5: '&#9679;&#9679;&#9679;&#9679;&#9679;',
    255: '',
  };
  slotSelector.querySelector('p.quality').innerHTML = QualityTable[data.quality];
}

function updateFrequency(slotSelector, data) {
  slotSelector.querySelector('p.frequency').innerHTML = data.frequency + ' Hz';
  if (data.frequency === '000000')
  {
    slotSelector.querySelector('.frequency').style.display = 'none';
  } else {
    slotSelector.querySelector('.frequency').style.display = 'block';
  }
}

function updateID(slotSelector, data) {
  slotSelector.querySelector('p.mic_id').innerHTML = data.id;
}

function updateName(slotSelector, data) {
  slotSelector.querySelector('p.name').innerHTML = data.name;
  updateBackground(slotSelector.querySelector('.mic_name'));
}

/* Possible values of `data.status`:
     'RX_COM_ERROR', 'AUDIO_PEAK', 'TX_COM_ERROR', 'TX_OFF', 'OK'

   For values of `data.battery_status`, see the keys of `BatteryStates` below.
*/
function updateStatus(slotSelector, data) {
  let status_class = data.status;
  if (['OK', 'TX_OFF'].includes(data.status) && data.battery_status != 'off') {
    status_class = data.battery_status.toUpperCase()
    if (data.status == 'TX_OFF') {
      status_class = 'PREV_' + status_class;
    }
  }

  slotSelector.querySelector('div.mic_name').className = 'mic_name';
  slotSelector.querySelector('div.mic_name').classList.add(status_class);

  slotSelector.querySelector('div.electrode').className = 'electrode';
  slotSelector.querySelector('div.electrode').classList.add(status_class);

  if (micboard.settingsMode !== 'EXTENDED') {
    if (data.status === 'RX_COM_ERROR') {
      slotSelector.querySelector('.chartzone').style.display = 'none';
      slotSelector.querySelector('.errorzone').style.display = 'block';
    } else {
      slotSelector.querySelector('.chartzone').style.display = 'block';
      slotSelector.querySelector('.errorzone').style.display = 'none';
    }
  }
}


function updateIP(slotSelector, data) {
  slotSelector.querySelector('p.ip').innerHTML = data.ip;
  slotSelector.querySelector('p.rxinfo').innerHTML = data.type + ' CH ' + data.channel;
}


const BatteryStates = {
  // Keep these keys in sync with the values of `WirelessMicBatteryStates` in py/mic/mic.py
  'good': 'batt_led_good',
  'replace': 'batt_led_warning',
  'critical': 'batt_led_danger',
  'off': 'batt_led_off',

  // These keys are used locally only
  'off_critical': 'batt_led_off_danger',
  'hidden': 'batt_led_hidden',
};

function updateBattery(slotSelector, data) {
  const batteryStateValues = Object.values(BatteryStates);
  const batteryBars = slotSelector.querySelectorAll('.battery-bar');
  batteryBars.forEach((b) => {
    b.classList.remove(...batteryStateValues);
  });

  let idx = 1;
  for (; idx <= Math.min(data.battery, data.battery_segments, batteryBars.length); ++idx) {
    slotSelector.querySelector('.battery-bar-' + idx).classList.add(BatteryStates[data.battery_status]);
  }
  for (; idx <= Math.min(data.battery_segments, batteryBars.length); ++idx) {
    if (data.battery_status == 'critical')
      slotSelector.querySelector('.battery-bar-' + idx).classList.add(BatteryStates.off_critical);
    else
      slotSelector.querySelector('.battery-bar-' + idx).classList.add(BatteryStates.off);
  }
  for (; idx <= batteryBars.length; ++idx) {
    slotSelector.querySelector('.battery-bar-' + idx).classList.add(BatteryStates.hidden);
  }

  if (micboard.group !== 0) {
    let hideChart = false;

    if (micboard.groups[micboard.group]) {
      hideChart = micboard.groups[micboard.group]['hide_charts'];
    }

    if (hideChart) {
      if (data.battery === 255) {
        slotSelector.querySelector('.slotgraph').style.display = 'none';
      } else {
        slotSelector.querySelector('.slotgraph').style.display = 'block';
      }
    }
  }
}


function updateDiversity(slotSelector, data) {
  const div = slotSelector.querySelector('.diversity');
  let newBar = '';
  for (let i = 0; i < data.antenna.length; i += 1) {
    const char = data.antenna.charAt(i);
    switch (char) {
      case 'A':
      case 'B': newBar += '<div class="diversity-bar diversity-bar-blue"></div>';
        break;
      case 'R': newBar += '<div class="diversity-bar diversity-bar-red"></div>';
        break;
      case 'X': newBar += '<div class="diversity-bar diversity-bar-off"></div>';
        break;
      default:
        break;
    }
  }
  div.innerHTML = newBar;
}

function updateCheck(data, key, callback) {
  if (key in data) {
    if (micboard.transmitters[data.slot][key] !== data[key]) {
      if (callback) {
        callback();
      }
      micboard.transmitters[data.slot][key] = data[key];
    }
  }
}


function updateSelector(slotSelector, data) {
  updateCheck(data, 'id', () => {
    updateID(slotSelector, data);
  });
  updateCheck(data, 'name', () => {
    updateName(slotSelector, data);
  });
  updateCheck(data, 'name_raw');
  updateCheck(data, 'status', () => {
    updateStatus(slotSelector, data);
  });
  updateCheck(data, 'battery', () => {
    updateBattery(slotSelector, data);
    updateStatus(slotSelector, data);
  });
  updateCheck(data, 'runtime', () => {
    updateRuntime(slotSelector, data);
  });
  updateCheck(data, 'antenna', () => {
    updateDiversity(slotSelector, data);
  });
  updateCheck(data, 'tx_offset', () => {
    updateTXOffset(slotSelector, data);
  });
  updateCheck(data, 'quality', () => {
    updateQuality(slotSelector, data);
  });
  updateCheck(data, 'frequency', () => {
    updateFrequency(slotSelector, data);
  });
  updateCheck(data, 'power_lock', () => {
    updatePowerlock(slotSelector, data);
  });
}


export function updateViewOnly(slotSelector, data) {
  if ('status' in data) {
    updateStatus(slotSelector, data);
  }
  if ('id' in data) {
    updateID(slotSelector, data);
  }
  if ('name' in data) {
    updateName(slotSelector, data);
  }
  if ('tx_offset' in data) {
    updateTXOffset(slotSelector, data);
  }
  if ('battery' in data) {
    updateBattery(slotSelector, data);
  }
  if ('runtime' in data) {
    updateRuntime(slotSelector, data);
  }
  if ('quality' in data) {
    updateQuality(slotSelector, data);
  }
  if ('frequency' in data) {
    updateFrequency(slotSelector, data);
  }
  if ('antenna' in data) {
    updateDiversity(slotSelector, data);
  }
  if ('ip' in data) {
    updateIP(slotSelector, data);
  }
  if ('power_lock' in data) {
    updatePowerlock(slotSelector, data);
  }
}

export function updateSlot(data) {
  if (document.getElementById('micboard').classList.contains('uploadmode')) {
    return;
  }

  if (data.slot === 0) {
    return;
  }
  const slot = 'slot-' + data.slot;
  const slotSelector = document.getElementById(slot);
  if (slotSelector) {
    updateSelector(slotSelector, data);
  }
}

export function renderDisplayList(dl) {
  console.log('DL :');
  console.log(dl);
  document.getElementById('micboard').innerHTML = '';

  if (micboard.url.demo) {
    seedTransmitters(dl);
    autoRandom();
  }

  const tx = micboard.transmitters;
  dl.forEach((e) => {
    let t;
    if (e !== 0) {
      if (typeof tx[e] !== 'undefined') {
        t = document.getElementById('column-template').content.cloneNode(true);
        t.querySelector('div.col-sm').id = 'slot-' + tx[e].slot;
        updateViewOnly(t, tx[e]);
        charts[tx[e].slot] = initChart(t, tx[e]);
        document.getElementById('micboard').appendChild(t);
      }
    } else {
      t = document.getElementById('column-template').content.cloneNode(true);
      t.querySelector('p.name').innerHTML = 'BLANK';
      t.querySelector('.col-sm').classList.add('blank');
      document.getElementById('micboard').appendChild(t);
    }
  });

  infoToggle();
}

export function renderGroup(group) {
  if (micboard.settingsMode === 'CONFIG') {
    document.getElementById('micboard').style.display = 'grid'
    document.getElementsByClassName('settings')[0].style.display = 'none'
  }
  micboard.group = group;
  updateHash();
  if (group === 0) {
    micboard.displayList = allSlots();
    renderDisplayList(micboard.displayList);
    updateEditor(group);
    return;
  }
  const out = micboard.groups[group];
  if (out) {
    micboard.displayList = out.slots;
    renderDisplayList(micboard.displayList);
    updateEditor(group);
  } else {
    micboard.displayList = [];
    renderDisplayList(micboard.displayList);
    updateEditor(group);
  }
}
