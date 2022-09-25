export default function betterFileSize(size: number) {
  if (size == 0) {
    return "0 MB"
  }
  const i = Math.floor(Math.log(size) / Math.log(1024))
  const convertedSize = size / Math.pow(1024, i)
  return convertedSize.toFixed(2) + " " + ["B", "kB", "MB", "GB", "TB"][i]
}
