import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders SOC shell branding", () => {
  render(<App />);
  expect(screen.getByText(/Intelligent Cyber Defense Framework/i)).toBeInTheDocument();
});
