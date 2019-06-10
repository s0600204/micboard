import { micboard, updateHash } from './app';

import { updateGIFBackgrounds } from './gif';

function swapClass(selector, currentClass, newClass) {
  selector.classList.remove(currentClass);
  selector.classList.add(newClass);
}


function setBackground(mode) {
  micboard.backgroundMode = mode;
  $('#micboard .mic_name').css('background-image', '');
  $('#micboard .mic_name').css('background-size', '');
  updateGIFBackgrounds();
  updateHash();
}


export function setDisplayMode(mode) {
  const selector = document.getElementById('container');
  swapClass(selector, micboard.displayMode, mode);
  micboard.displayMode = mode;
}


export function toggleDisplayMode() {
  switch (micboard.displayMode) {
    case 'deskmode': setDisplayMode('tvmode');
      break;
    case 'tvmode': setDisplayMode('deskmode');
      setBackground('NONE');
      break;
    default:
      break;
  }
  updateHash();
}


export function toggleBackgrounds() {
  if (micboard.displayMode === 'tvmode') {
    switch (micboard.backgroundMode) {
      case 'NONE': setBackground('MP4');
        break;
      case 'MP4': setBackground('IMG');
        break;
      case 'IMG': setBackground('NONE');
        break;
      default: break;
    }
  }
}


function setInfoDrawer(mode) {
  const selector = document.getElementById('micboard');
  swapClass(selector, micboard.infoDrawerMode, mode);
  micboard.infoDrawerMode = mode;
  setDisplayMode('tvmode');
  updateHash();
}


export function toggleInfoDrawer() {
  switch (micboard.infoDrawerMode) {
    case 'elinfo00': setInfoDrawer('elinfo01');
      break;
    case 'elinfo01': setInfoDrawer('elinfo10');
      break;
    case 'elinfo10': setInfoDrawer('elinfo11');
      break;
    case 'elinfo11': setInfoDrawer('elinfo00');
      break;
    default:
      break;
  }
}
