/**
 * Utilidad para validar NIF/CIF españoles
 */

/**
 * Valida un NIF/CIF español
 * @param value El NIF/CIF a validar
 * @returns Un objeto con el resultado de la validación y un mensaje de error si corresponde
 */
export const validateNifCif = (value: string): { isValid: boolean; message?: string } => {
  if (!value) {
    return { isValid: false, message: 'El NIF/CIF es obligatorio' };
  }

  // Normalizar: eliminar espacios y convertir a mayúsculas
  const nifCif = value.trim().toUpperCase();

  // Validar formato general
  if (!/^[A-Z0-9]{9}$/.test(nifCif)) {
    return { isValid: false, message: 'El formato del NIF/CIF no es válido (debe tener 9 caracteres)' };
  }

  // Validar NIF (persona física)
  if (/^[0-9]{8}[A-Z]$/.test(nifCif)) {
    const number = nifCif.substring(0, 8);
    const letter = nifCif.charAt(8);
    const validLetters = 'TRWAGMYFPDXBNJZSQVHLCKE';
    const calculatedLetter = validLetters.charAt(parseInt(number, 10) % 23);

    if (letter !== calculatedLetter) {
      return { isValid: false, message: `La letra del NIF no es correcta. Debería ser ${calculatedLetter}` };
    }

    return { isValid: true };
  }

  // Validar NIE (extranjeros)
  if (/^[XYZ][0-9]{7}[A-Z]$/.test(nifCif)) {
    const firstChar = nifCif.charAt(0);
    const number = nifCif.substring(1, 8);
    const letter = nifCif.charAt(8);
    
    // Reemplazar X, Y, Z por 0, 1, 2
    let modifiedNumber = number;
    if (firstChar === 'X') modifiedNumber = '0' + number;
    else if (firstChar === 'Y') modifiedNumber = '1' + number;
    else if (firstChar === 'Z') modifiedNumber = '2' + number;
    
    const validLetters = 'TRWAGMYFPDXBNJZSQVHLCKE';
    const calculatedLetter = validLetters.charAt(parseInt(modifiedNumber, 10) % 23);

    if (letter !== calculatedLetter) {
      return { isValid: false, message: `La letra del NIE no es correcta. Debería ser ${calculatedLetter}` };
    }

    return { isValid: true };
  }

  // Validar CIF (empresas)
  if (/^[ABCDEFGHJKLMNPQRSUVW][0-9]{7}[0-9A-J]$/.test(nifCif)) {
    const firstChar = nifCif.charAt(0);
    const number = nifCif.substring(1, 8);
    const controlChar = nifCif.charAt(8);
    
    // Calcular dígito de control
    let sum = 0;
    for (let i = 0; i < number.length; i++) {
      const digit = parseInt(number.charAt(i), 10);
      if (i % 2 === 0) {
        // Posiciones pares (0, 2, 4, 6)
        let temp = digit * 2;
        if (temp > 9) {
          temp = Math.floor(temp / 10) + (temp % 10);
        }
        sum += temp;
      } else {
        // Posiciones impares (1, 3, 5)
        sum += digit;
      }
    }
    
    const controlDigit = (10 - (sum % 10)) % 10;
    const controlLetter = 'JABCDEFGHI'.charAt(controlDigit);
    
    // Para CIF, el control puede ser un número o una letra
    if (/[0-9]/.test(controlChar)) {
      if (parseInt(controlChar, 10) !== controlDigit) {
        return { isValid: false, message: `El dígito de control del CIF no es correcto. Debería ser ${controlDigit}` };
      }
    } else {
      if (controlChar !== controlLetter) {
        return { isValid: false, message: `La letra de control del CIF no es correcta. Debería ser ${controlLetter}` };
      }
    }
    
    return { isValid: true };
  }

  return { isValid: false, message: 'El formato del NIF/CIF no es reconocido' };
};

/**
 * Formatea un NIF/CIF para mostrarlo con el formato correcto
 * @param value El NIF/CIF a formatear
 * @returns El NIF/CIF formateado
 */
export const formatNifCif = (value: string): string => {
  if (!value) return '';
  
  // Eliminar espacios y convertir a mayúsculas
  let formatted = value.trim().toUpperCase();
  
  // Eliminar caracteres no alfanuméricos
  formatted = formatted.replace(/[^A-Z0-9]/g, '');
  
  return formatted;
};
