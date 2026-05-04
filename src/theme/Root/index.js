import BackToTop from "@components/BackToTop";

export default function Root({ children }) {
  return (
    <>
      {children}
      <BackToTop />
    </>
  );
}
