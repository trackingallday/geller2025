const prepString = (str) => {
  return str.replace(" ", "").toLowerCase();
}

export function alphabetSort(a, b) {
  const aa = prepString(a);
  const bb = prepString(b);
  if(aa === bb) {
    return 0;
  }
  return aa < bb ? -1 : 1
}
