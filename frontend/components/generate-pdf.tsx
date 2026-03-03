import jsPDF from "jspdf"

interface Message {
  role: 'user' | 'assistant'
  content: string
}
// https://www.geeksforgeeks.org/html/how-to-generate-pdf-file-using-jspdf-library/
export function generatePDF(messages: Message[], title: string = "EduBot Notes"): void {
  const doc = new jsPDF()
  
  let y = 20 // vertical position
  
  // Title
  doc.setFontSize(18)
  doc.text(title, 20, y)
  y += 10
  
  // Date
  doc.setFontSize(10)
  doc.text(`Generated: ${new Date().toLocaleString()}`, 20, y)
  y += 15

  messages.forEach((msg) => {
    if (y > 270) { // naya page
      doc.addPage()
      y = 20
    }

    if (msg.role === 'user') {
      doc.setFontSize(11)
      doc.setTextColor(100, 100, 255) // blue
      doc.text("You:", 20, y)
    } else {
      doc.setFontSize(11)
      doc.setTextColor(0, 150, 0) // green
      doc.text("EduBot:", 20, y)
    }
    y += 7

    // Content wrap karo
    doc.setTextColor(0, 0, 0)
    doc.setFontSize(10)
    const lines = doc.splitTextToSize(msg.content, 170)
    doc.text(lines, 20, y)
    y += lines.length * 6 + 5
  })

  doc.save("edubot-notes.pdf")
}