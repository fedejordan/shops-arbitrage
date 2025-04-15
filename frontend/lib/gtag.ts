export const GA_MEASUREMENT_ID = 'G-3DQX8E6ME0'; // tu ID real

// Page view
export const pageview = (url: string) => {
  window.gtag('config', GA_MEASUREMENT_ID, {
    page_path: url,
  });
};

// Event
export const event = ({ action, category, label, value }: {
  action: string,
  category: string,
  label: string,
  value: number
}) => {
  window.gtag('event', action, {
    event_category: category,
    event_label: label,
    value: value,
  });
};
