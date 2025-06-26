'use strict';

import { Sortable, Plugins } from '@shopify/draggable';

import { micboard, updateHash } from './app.js';
import { postJSON } from './data.js';

const TYPE_SEPARATOR = '__';
const OFFLINE_TYPE_VALUE = 'offline';

function buildTypeValue(data) {
  if (data.type == OFFLINE_TYPE_VALUE)
    return data.type;
  return data.type + TYPE_SEPARATOR + data.model;
}

function splitTypeValue(value) {
  return value.split(TYPE_SEPARATOR);
}

function updateEditEntry(slotSelector, data) {
  if (data.ip) {
    slotSelector.querySelector('.cfg-ip').value = data.ip;
  }
  slotSelector.querySelector('.cfg-type').value = buildTypeValue(data);

  const channelInput = slotSelector.querySelector('.cfg-channel');
  updateChannelCount(channelInput, data.type, data.model);
  channelInput.value = data.channel;
  console.log(data);
}


function getMaxSlot() {
  let max = 0;
  micboard.config.slots.forEach((e) => {
    if (e.slot > max) {
      max = e.slot;
    }
  });
  return max;
}


function updateSlotID() {
  const configList = document.querySelectorAll('#editor_holder .cfg-row');
  let i = 1;
  configList.forEach((t) => {
    t.querySelector('.slot-number label').innerHTML = 'slot ' + i;
    t.id = 'editslot-' + i;
    i += 1;
  });
}

function dragSetup() {
  const containerSelector = '#discovered_list, #editor_holder';
  const containers = document.querySelectorAll(containerSelector);

  if (containers.length === 0) {
    return false;
  }

  const sortable = new Sortable(containers, {
    draggable: '.cfg-row',
    handle: '.navbar-dark',
    mirror: {
      constrainDimensions: true,
    },
    plugins: [Plugins.ResizeMirror],
  });

  // sortable.on('sortable:start', () => console.log('drag:start'));
  // sortable.on('sortable:move', () => console.log('drag:move'));
  sortable.on('drag:stop', () => {
    setTimeout(updateSlotID, 125);
  });
}

function renderSlotList() {
  const config = micboard.config.slots;
  const slotCount = getMaxSlot() + 4;
  let t;

  document.getElementById('editor_holder').innerHTML = '';

  for (let i = 1; i <= slotCount; i += 1) {
    t = document.getElementById('config-slot-template').content.cloneNode(true);
    t.querySelector('label').innerHTML = 'slot ' + i;
    t.querySelector('.cfg-row').id = 'editslot-' + i;
    populateTypeSelect(t.querySelector('.cfg-type'));
    document.getElementById('editor_holder').append(t);
  }

  config.forEach((e) => {
    const slotID = 'editslot-' + e.slot;
    t = document.getElementById(slotID);
    updateEditEntry(t, e);
  });
}


function discoverFilter(item, currentSlotList) {
  let out = true;
  currentSlotList.forEach((e) => {
    if ((e.ip === item.ip) && (e.type === item.type) && (e.channel === item.channel)) {
      out = false;
    }
  });
  return out;
}

function renderDiscoverdDeviceList() {
  const discovered = micboard.discovered;
  const currentSlotList = generateJSONConfig();

  let t;

  document.getElementById('discovered_list').innerHTML = '';

  discovered.forEach((e) => {
    for (let i = 1; i <= e.channels; i += 1) {
      e.channel = i;
      if (discoverFilter(e, currentSlotList)) {
        t = document.getElementById('config-slot-template').content.cloneNode(true);
        populateTypeSelect(t.querySelector('.cfg-type'));
        updateEditEntry(t, e);
        document.getElementById('discovered_list').append(t);
      }
    }
  });
}

function generateJSONConfig() {
  const slotList = [];
  const configBoard = document.getElementById('editor_holder').getElementsByClassName('cfg-row');

  for (let i = 0; i < configBoard.length; i += 1) {
    const slot = parseInt(configBoard[i].id.replace(/[^\d.]/g, ''), 10);
    if (slot && (slotList.indexOf(slot) === -1)) {
      const output = {};

      output.slot = slot;
      [output.type, output.model] = splitTypeValue(configBoard[i].querySelector('.cfg-type').value);

      if (micboard.ALL_MODELS.includes(output.type)) {
        output.ip = configBoard[i].querySelector('.cfg-ip').value;
        output.channel = parseInt(configBoard[i].querySelector('.cfg-channel').value, 10);
      }

      if (output.type) {
        slotList.push(output);
      }
    }
  }
  return slotList;
}


function addAllDiscoveredDevices() {
  const devices = document.querySelectorAll('#discovered_list .cfg-row');
  const cfg_list = document.getElementById('editor_holder');
  const top = cfg_list.querySelector('.cfg-row');

  devices.forEach((e) => {
    cfg_list.insertBefore(e, top);
  });
  updateSlotID();
}

function updateHiddenSlots() {
  const cfgRows = document.querySelectorAll('#editor_holder .cfg-row')
  Array.from(cfgRows).forEach((e) => {
    const type = e.querySelector('.cfg-type').value
    if ( type === 'offline' || type === '') {
      e.querySelector('.cfg-ip').style.display = "none"
      e.querySelector('.cfg-channel').style.display = "none"
    } else {
      e.querySelector('.cfg-ip').style.display = "block"
      e.querySelector('.cfg-channel').style.display = "block"
      updateChannelCount(e.querySelector('.cfg-channel'), ...splitTypeValue(type));
    }
  })
}

function updateChannelCount(channelDOM, type, model) {
  const previousValue = channelDOM.value;
  const channelLimit = micboard.MODEL_INFO[type].models[model].channels;
  while (channelDOM.firstChild)
    channelDOM.removeChild(channelDOM.firstChild);

  for (let chan = 0; chan < channelLimit; ++chan) {
    const channelOption = document.createElement('option');
    channelOption.text = chan + 1;
    channelDOM.appendChild(channelOption);
  }
  channelDOM.value = Math.min(Math.max(1, previousValue), channelLimit);
}

function populateTypeSelect(selectDOM) {
  selectDOM.appendChild(document.createElement('option'));

  for (let type in micboard.MODEL_INFO) {
    const typeInfo = micboard.MODEL_INFO[type];
    const group = document.createElement('optgroup');
    group.label = typeInfo.name;

    for (let model in typeInfo.models) {
      const modelInfo = typeInfo.models[model];
      const option = document.createElement('option');
      option.value = [type, model].join(TYPE_SEPARATOR);
      option.innerHTML = modelInfo.name;
      group.appendChild(option);
    }

    selectDOM.appendChild(group);
  }

  const offlineOption = document.createElement('option');
  offlineOption.text = 'Offline'; // @todo: l10n
  offlineOption.value = 'offline';
  selectDOM.appendChild(offlineOption);
}

export function initConfigEditor() {
  if (micboard.settingsMode === 'CONFIG') {
    console.log('oh that explains it!')
    return;
  }

  micboard.settingsMode = 'CONFIG';
  updateHash();
  document.getElementById('micboard').style.display = "none"
  document.querySelector('.settings').style.display = "block"

  renderSlotList();
  renderDiscoverdDeviceList();

  dragSetup();



  updateHiddenSlots();
  
  const cfgTypeInputs = document.getElementsByClassName('cfg-type')
  Array.from(cfgTypeInputs).forEach((e) => {
    e.addEventListener('change', () => updateHiddenSlots())
  })

  document.getElementById('add-discovered').addEventListener('click', () => {
    addAllDiscoveredDevices();
  });

  document.getElementById('save').addEventListener('click', ()=> {
    const data = generateJSONConfig();
    const url = 'api/config';
    console.log(data);
    postJSON(url, data, () => {
      micboard.settingsMode = 'NONE';
      updateHash();
      window.location.reload();
    });
  });

  const delBtns = document.querySelectorAll('#editor_holder .del-btn')
  Array.from(delBtns).forEach((btn) => {
    btn.addEventListener('click', (e) => {
      const row = e.target.closest('.cfg-row').remove()
      updateSlotID();
      renderDiscoverdDeviceList();
    })
  });

  document.getElementById('clear-config').addEventListener('click', () => {
    const cfg_list = document.querySelectorAll('#editor_holder .cfg-row')
    Array.from(cfg_list).forEach(e => e.remove())
    let t;
    for (let i = 0; i < 4; i += 1) {
      t = document.getElementById('config-slot-template').content.cloneNode(true);
      populateTypeSelect(t.querySelector('.cfg-type'));
      document.getElementById('editor_holder').append(t);
    }
    updateSlotID();
    updateHiddenSlots();
    renderDiscoverdDeviceList();
  });

  document.getElementById('add-config-row').addEventListener('click', () => {
    const t = document.getElementById('config-slot-template').content.cloneNode(true);
    document.getElementById('editor_holder').append(t);
    updateSlotID();
    updateHiddenSlots();
  });
}
