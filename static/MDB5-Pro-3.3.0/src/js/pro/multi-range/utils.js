// eslint-disable-next-line import/prefer-default-export
export const getEventTypeClientX = (ev) => {
  const event = ev.type === 'touchmove' ? ev.touches[0].clientX : ev.clientX;

  return event;
};
