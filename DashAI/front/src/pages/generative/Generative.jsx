import { TourProvider } from "../../components/tour/TourProvider";
import { TOUR_KEYS } from "../../constants/tours";
import GenerativeContent from "./GenerativeContent";

export default function Generative() {
  return (
    <TourProvider tourKey={TOUR_KEYS.GENERATIVE}>
      <GenerativeContent />
    </TourProvider>
  );
}
