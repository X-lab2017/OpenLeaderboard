import { Button } from 'antd';
import { VerticalAlignTopOutlined } from '@ant-design/icons';
function scrollToTop(timestamp) {
  let scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: 'smooth',
  });
}
const ScrollTopButton = (props) => {
  return (
    <Button
      style={{
        position: 'fixed',
        zIndex: 2147483640,
        right: '22px',
        bottom: '60px',
        backgroundColor: '#FFCC19',
        borderColor: '#FFCC19',
      }}
      type="primary"
      icon={<VerticalAlignTopOutlined />}
      onClick={() => {
        console.log('hi');
        window.requestAnimationFrame(scrollToTop);
      }}
    />
  );
};
export default ScrollTopButton;
