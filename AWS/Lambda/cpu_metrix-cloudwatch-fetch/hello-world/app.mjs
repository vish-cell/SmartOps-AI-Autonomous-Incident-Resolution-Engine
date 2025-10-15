import * as fs from 'fs/promises'; // Use promises API for asynchronous I/O
import * as path from 'path';

// ====== PATHS & CONFIGURATION (Simulated Local Paths) ======
// This path is relative to the directory where SAM mounts the code (e.g., C:\...\cpu_metrix-cloudwatch-fetch)
const CLOUDWATCH_DIR = path.join('AWS', 'cloudwatch');

/**
 * Converts timestamp from Python format (YYYY-MM-DD HH:MM:SS) 
 * to CloudWatch ISO format (YYYY-MM-DDTHH:MM:SSZ).
 */
function formatTsForCloudwatch(tsStr) {
    if (typeof tsStr !== 'string') return null;
    return tsStr.replace(' ', 'T') + 'Z';
}

/**
 * Simulates the log analysis: reads logs from CLOUDWATCH_DIR, finds corresponding entries, 
 * and groups them by instance ID.
 * @param {string[]} anomalyTimestampsList - List of timestamps marked as anomalous 
 * (format: YYYY-MM-DD HH:MM:SS).
 * @returns {Promise<Object>} - Grouped logs by instance ID in the requested output format.
 */
async function analyzeCloudwatchLogs(anomalyTimestampsList) {
    if (!anomalyTimestampsList || anomalyTimestampsList.length === 0) {
        console.log("No anomaly timestamps provided for analysis.");
        return {};
    }
    
    const anomTsSet = new Set(anomalyTimestampsList.map(formatTsForCloudwatch));
    const groupedAnomalousLogs = {};

    try {
        const files = await fs.readdir(CLOUDWATCH_DIR); // Asynchronous read directory
        
        if (files.length === 0) {
            console.warn(`CloudWatch directory ${CLOUDWATCH_DIR} is empty.`);
            return {};
        }

        for (const file of files) {
            if (file.endsWith(".json")) {
                const filePath = path.join(CLOUDWATCH_DIR, file);
                let logData;
                
                try {
                    const fileContent = await fs.readFile(filePath, 'utf8'); // Asynchronous read file
                    logData = JSON.parse(fileContent); 
                } catch (e) {
                    console.error(`Error loading/parsing CloudWatch JSON from ${filePath}: ${e.message}`);
                    continue;
                }

                if (!Array.isArray(logData)) continue;

                for (const logEntry of logData) {
                    const logTimestamp = logEntry.timestamp;
                    const instanceId = logEntry.instance_id;

                    if (instanceId && logTimestamp && anomTsSet.has(logTimestamp)) {
                        
                        const outputLog = {
                            "timestamp": logTimestamp,
                            "level": logEntry.level,
                            "msg": logEntry.msg,
                            "reason": `Correlated with Metric Anomaly` 
                        };
                        
                        if (!groupedAnomalousLogs[instanceId]) {
                            groupedAnomalousLogs[instanceId] = [];
                        }
                        groupedAnomalousLogs[instanceId].push(outputLog);
                    }
                }
            }
        }
    } catch (e) {
        if (e.code === 'ENOENT') {
            console.error(`ERROR: CloudWatch logs directory not found at ${CLOUDWATCH_DIR}.`);
        } else {
            console.error(`Unexpected error during file processing: ${e.message}`);
        }
        return {};
    }

    return groupedAnomalousLogs;
}


export const lambdaHandler = async (event, context) => {
    let anomalyFilePath;
    let anomalyTimestamps = [];
    
    // --- STEP 1: Parse the API Gateway Event Body to find the file path ---
    try {
        if (event && event.body && typeof event.body === 'string') {
             // API Gateway path: body is a stringified JSON object
             const requestBody = JSON.parse(event.body);
             anomalyFilePath = requestBody.anomalies_path;
        } else if (event && event.anomalies_path) {
             // Direct invoke path: path is at the top level
             anomalyFilePath = event.anomalies_path;
        } else {
             throw new Error("Missing 'anomalies_path' in the event or request body.");
        }
    } catch (error) {
        console.error("Error processing event payload to find path:", error);
        return {
            statusCode: 400,
            body: JSON.stringify({ 
                message: `Failed to find path in event: ${error.message}` 
            })
        };
    }
    
    // --- STEP 2: Read the Anomaly Timestamps file from the path ---
    try {
        const fileContent = await fs.readFile(anomalyFilePath, 'utf8'); // Asynchronous read
        anomalyTimestamps = JSON.parse(fileContent);

        if (!Array.isArray(anomalyTimestamps)) {
             throw new Error("Anomaly file content is not a JSON array of timestamps.");
        }

    } catch (error) {
        console.error(`Error loading anomaly file at ${anomalyFilePath}:`, error);
        return {
            statusCode: 404,
            body: JSON.stringify({ 
                message: `Failed to load anomaly timestamps file: ${error.message}` 
            })
        };
    }
    
    // --- STEP 3: Execute the log analysis function ---
    const analyzedLogs = await analyzeCloudwatchLogs(anomalyTimestamps); // Await the async function

    // 4. Return the grouped log data in API Gateway format
    const response = {
        statusCode: 200,
        body: JSON.stringify(analyzedLogs) 
    };

    return response;
};
